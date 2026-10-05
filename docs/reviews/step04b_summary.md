# Build step 4b — summary for review

Date: 2026-10-05. Branch: `step-04b-assumptions`. **Status: built, suite green; awaiting the second-model review.** A small step before step 5, on the owner's instruction: an assumptions register and a read-only page for it. It is not a PRD Section 15 step.

The suite is the gate. This summary is for the second-model review (PRD 13.2), which uses `docs/reviews/checklist.md`.

The owner approved the plan on 2026-10-05, after six questions (below), with additions: nine more entries and a summary line on the page. After the first build, the owner decided the one open entry, the Texas A&M microstructure (section "The owner's decision on the Texas A&M microstructure"); the register and this summary were updated, with no code that applies it.

**Not built, as instructed:**
- applying any of the eight decisions in code;
- recomputing the reference numbers;
- any other screen;
- any migration.

There is no change to `render.yaml`, `.github/workflows/`, the Dockerfile, Compose, dependencies or the migration.

## What was built

| Path | What it is |
|---|---|
| `hypocurate/assumptions.json` | **The register: one source file**, a JSON list with one object per assumption (the same pattern as `docs/glossary.json`). 60 entries, all in force; no open decision since the owner's decision on the Texas A&M microstructure. |
| `hypocurate/assumptions.py` | It provides:<br>• `load_register()` and `validate()`: the schema, in plain Python with no new dependency;<br>• `resolve_setting()` and `check_settings()`: the named settings in code;<br>• `page_sections()` and `summary_counts()`: what the page shows. |
| `hypocurate/web/app.py` | `GET /assumptions`:<br>• behind the existing login middleware (nothing new is public);<br>• no other method: POST, PUT, PATCH and DELETE give 405;<br>• the register is read and validated once when the service starts, so **an invalid register stops the service starting**;<br>• `create_app` takes an optional `register` for tests, and validates it too. |
| `hypocurate/web/templates/assumptions.html` | The page:<br>• a summary line (entries, open decisions, scientific assumptions not reviewed by an expert);<br>• open decisions first, then one table per category (scientific, statistical, data handling, operational);<br>• columns: assumption and statement, value, what it affects, expert review, applied in code;<br>• each unreviewed scientific entry has a red left border and the badge "Not reviewed by an expert";<br>• each row expands (`<details>`, no JavaScript) to the reason, evidence, who decided and when, sensitivity analysis, the named settings or the step, earlier values, notes and the key;<br>• a filter `?review=not_reviewed` ("Show only: not reviewed by an expert" / "Show all");<br>• the only form is "Sign out". |
| `hypocurate/web/templates/base.html` | A `main_attrs` block, so this page can widen `<main>`. The other pages render as before. |
| `hypocurate/web/templates/home.html` | A link to Assumptions. |
| `hypocurate/web/static/style.css` | Plain table and badge styles in the login page's colours, with a narrow-screen layout. Full styling and the per-run "assumptions in force" panel come at step 10. |
| `scripts/check_runtime_image.py` | `REQUIRED` gains the register, its module and the template, so the deployed image must contain the page. |
| `CLAUDE.md` | "How we work":<br>• **item 11**: any new assumption or changed default enters the register in the same merge;<br>• **item 12**: code reads a default from one named place, never a scattered literal; an "applied: yes" entry names it, and `tests/test_assumptions.py` fails if it does not exist or holds a different value. |
| `tests/test_assumptions.py` | 58 tests (below). |

## The register's schema

Every entry has these fields. Unknown fields are refused, and so are missing ones.

| Field | Content |
|---|---|
| `key` | Lower-case identifier, unique. |
| `name`, `statement` | A short name and a plain-English statement. |
| `state` | `in_force` or `open` (an open decision has `value: null`, `decided: null` and `pending: {by, before_step}`). |
| `value` | `{text, unit}`; unit may be null. |
| `category` | `scientific`, `statistical`, `data_handling` or `operational`. |
| `affects` | What it affects. |
| `reason`, `evidence` | The reason, and a non-empty list of evidence or citations. |
| `decided` | `{by, date}`. |
| `expert_review` | `{status, name, date}`, where status is `not_reviewed` (no name or date), `accepted` or `disputed` (both need a name and a date). |
| `sensitivity` | The sensitivity analysis that covers it, or null. |
| `applied` | Either `{status: "yes", settings: [{ref, equals?}…], note}`, with at least one named setting, or `{status: "not_yet", step: 5–12, note}`. |
| `history` | Earlier values `{value, from, to, note}`, in date order, ending no later than the current decision. |
| `notes` | PRD conflicts and open points. |

**Named settings** (`ref`) have one of four forms:

| Form | Example |
|---|---|
| `python:<module>:<name>[.<attribute or key>…]` | `python:hypocurate.sources.versions:SOURCES.tamu_fcc.grouping_unit` |
| `python:<module>:<function>(<parameter>)` | `python:hypocurate.db.retry:run_transaction(attempts)`, the parameter's default |
| `sql:<name>` | `sql:ck_source_file_max_size`, a whole word in the migrations |
| `file:<repository path>:<text>` | `file:Dockerfile:--workers 1` |

An optional `equals` gives the value the code must hold. Sets are compared sorted and tuples as lists.

## The entries (60)

Who decided, abbreviated:
- **Owner**: owner (Khalid El-Awady);
- **PRD**: PRD v1.6 (owner);
- **Ref.**: reference script and PRD v1.6 (owner);
- **Implicit**: "implicit in PRD v1.6 and the reference script" (the owner's wording).

Every entry's expert review is **not reviewed**.

### The owner's decision on the Texas A&M microstructure (2026-10-05, after the first build)
| Key | Category | Value | Applied |
|---|---|---|---|
| `tamu_microstructure` | scientific | single-phase FCC, **assigned by decision** | not yet: step 6 |

It was the one open decision in the first build (`state: open`, pending the owner before step 6); its history records that.

### The owner's eight decisions of 2026-10-05
| Key | Category | Value | Applied |
|---|---|---|---|
| `tamu_test_temperature` (a) | scientific | room temperature, **assigned by decision** | not yet: step 6 |
| `permitted_test_types` (b) | scientific | tension only; sensitivity "tension and compression together" | not yet: step 6 |
| `tamu_grouping_unit` (c) | statistical | one group (the dataset); sensitivity "six batches as six groups" | **yes**: `SOURCES.tamu_fcc.grouping_unit == "dataset"` (the sensitivity analysis is step 7's) |
| `same_alloy_rule` (d) | scientific | round to 0.1 at.%, same alloy when the rounded compositions are identical; sensitivity at 1 at.% | not yet: step 6 |
| `fixed_minimums` (e) | statistical | 30 records; 5 alloys; 10 papers; 10 residual df | not yet: step 6 (plan default; check in step 7) |
| `values_disagree_tolerance` (f) | data handling | > 2%, relative to the smaller value | not yet: step 6 |
| `calibration_noise_levels` (g) | statistical | estimated from frozen residuals by a method fixed at the rules lock; smallest effect default 150 | not yet: step 7 |
| `tag_starting_lists` (h) | data handling | the three lists as given | not yet: step 6 |

**"Unless you find otherwise":** decision c is already applied. The Texas A&M source definition has grouping unit `dataset`, and the adapter refuses any other unit (step 4).

### All other entries
| Category | Key | Decided by | Applied |
|---|---|---|---|
| scientific | `shared_coefficient`, `exponent_fixed`, `baseline_per_alloy`, `quasistatic_tests` | Implicit | not yet: 7, 7, 7, 6 |
| scientific | `grain_size_as_reported`, `yield_strength_as_reported`, `composition_as_reported` | Implicit | yes (`HARMONIZED_FIELDS` units) |
| scientific | `mean_grain_size_only` | Implicit | not yet: 7 |
| scientific | `model_form`, `alloy_eligibility`, `physical_validity_checks` | PRD | not yet: 7, 6, 6 |
| scientific | `room_temperature_scope` (20–25 °C), `fcc_microstructure_scope`, `grain_size_floor` (< 0.1 µm excluded) | Ref. | not yet: 6 (test side only today) |
| scientific | `tamu_test_type`, `tamu_phase_class` | Owner (step 4 rule) | yes (`TEST_TYPE_CITATION`, `PHASE_CITATION`) |
| statistical | `ols_alloy_intercepts`, `cluster_robust_se`, `one_sided_test`, `validity_checks`, `pooled_gives_verdict`, `calibration_simulation`, `reference_test_tolerance` | PRD | not yet: 7 |
| statistical | `p_threshold_comparison` (p < 0.05) | Owner, 2026-10-05 | not yet: 7 |
| statistical | `papers_independent` | Implicit | yes (`SOURCES.mpea.grouping_unit == "paper"`) |
| statistical | `normal_errors_in_calibration` | Implicit | not yet: 7 |
| statistical | `sufficiency_options` | PRD | yes (`ck_plan_sufficiency_option`, `ck_run_exploratory_needs_verdict`, `hc_run_update`) |
| statistical | `power_information_only` | Owner, step 3 | yes (`ck_plan_sufficiency_option`) |
| data handling | `tamu_composition_unit` | Owner (step 4 rule) | yes (`COMPOSITION_UNIT_CITATION`) |
| data handling | `mpea_microstructure_label_trusted`, `curated_values_trusted` | Implicit | yes (`HARMONIZED_FIELDS.microstructure`; `mpea_layout.read`) |
| data handling | `paper_grouping_by_doi`, `values_kept_as_reported`, `malformed_files_refused`, `composition_normalization`, `alloy_label_display_only`, `controlled_extract_disabled` | Owner, step 4 | yes |
| data handling | `assigned_value_statuses` | Owner, 2026-10-05 | not yet: 6 |
| data handling | `grain_size_transformation_at_analysis` | Owner, step 4 | not yet: 6 |
| data handling | `duplicate_identity`, `unresolved_duplicates`, `scope_not_confirmed` | PRD | not yet: 6 |
| data handling | `duplicate_survivor_rule` | Owner, step 1 | not yet: 6 |
| operational | `stored_file_limits`, `login_throttle`, `session_length`, `secret_lengths`, `single_web_process`, `transaction_retries`, `worker_poll_interval` | Owner, steps 2–4 | yes |
| operational | `spending_caps` | PRD | not yet: 9 |

**Added while writing the owner's additional entries** (the owner asked for others of this kind):
- `mean_grain_size_only`: the grain-size distribution width is not used. The Texas A&M source studies it as a predictor.
- `composition_as_reported`: nominal and measured compositions are not distinguished.
- `mpea_microstructure_label_trusted`: the compilation's phase label is taken as the phase constitution.

**Left out on purpose:**
- the CLAUDE.md "never break" rules, which are invariants, not assumptions: model recall never pooled, code decides, the checkpoints, the wording;
- the model per agent (PRD 17 #2, undecided; step 8);
- the storage estimate;
- Render plans and region.

**Keys renamed from the plan while writing:**

| Plan | Register |
|---|---|
| `same_alloy_tolerance` | `same_alloy_rule` |
| `calibration_assumptions` | `calibration_noise_levels` |
| `assigned_values_need_citation` | `assigned_value_statuses` |
| `password_lengths` | `secret_lengths` |
| `paper_grouping_doi` | `paper_grouping_by_doi` |
| `tamu_phase_fcc` | `tamu_phase_class` |
| `tamu_test_type_tension` | `tamu_test_type` |
| `sufficiency_default_option` | `sufficiency_options` |
| `calibration_simulations` | `calibration_simulation` |

## The owner's answers (2026-10-05)

1. **Decision g and PRD 5.10.**
   - Recorded as "the estimation method is fixed at the rules lock and applied by code after the dataset freeze; no person or agent chooses the values".
   - The notes record:
     - the conflict with PRD 5.10, which says these values are fixed at the rules lock and never estimated from the real outcomes;
     - that this is a **safeguard change needing a second-model review in step 7 before it is applied**;
     - the alternative to compare in that review: report calibration both ways, with data-derived noise levels and with the fixed defaults.
2. **Decision a and the rule for assigned values: two statuses.**
   - **"Assigned from source"** rests on an explicit quoted statement in the source's documentation.
   - **"Assigned by decision"** rests on a recorded owner or expert decision, citing its basis.
   - Entry `assigned_value_statuses` states the rule. Today the code has one status, `assigned`, which requires a citation and is used only for source statements; the split arrives in step 6.
   - Decision a is "assigned by decision".
   - **For step 6:** the reference plan names a sensitivity analysis that accepts only reported values and values assigned from source, so the effect of every decision-based assignment is visible.
3. **Decision d.**
   - It is stated as the rule that produced the reference numbers: round each element to the nearest 0.1 at.%; same alloy when the rounded compositions are identical. This is transitive by construction.
   - Known weakness: compositions closer than the step can fall into different bins at a boundary.
   - Sensitivity analysis: the same rule at 1 at.%.
   - The earlier wording "each within 0.1 at.%" appeared nowhere in the repository or the memory files; the register uses the corrected wording.
   - **For step 6, a possible improvement, not a decision:** tolerance-based grouping, which needs a stated rule for chains and the owner's approval.
4. **Decision f.**
   - Relative difference = |a − b| / min(|a|, |b|).
   - **The pairing is not stated as final.** Open point for step 6, to be settled with the owner's approval:
     - repeat specimens in one source (same paper, alloy, grain size and conditions) are legitimate separate measurements;
     - a conflict is two records claiming to be the same measurement that disagree, mainly different sources reporting the same paper.
5. **FCC scope:** first recorded as an open decision entry, with the phase-constitution search reported below. The owner then decided it (next section).
6. **p-value against the threshold: p < α**, decided now. This closes step 3's "p < vs ≤" item.

**Additions at approval:**
- the nine "implicit" entries, each with a statement and what it affects:
  - (a) `shared_coefficient`, with its note on the ≈427 vs ≈1173 per-source estimates and per-source estimates as its sensitivity analysis;
  - (b) `grain_size_as_reported`;
  - (c) `yield_strength_as_reported`;
  - (d) `exponent_fixed`;
  - (e) `baseline_per_alloy`;
  - (f) `quasistatic_tests`;
  - (g) `papers_independent`;
  - (h) `curated_values_trusted`;
  - (i) `normal_errors_in_calibration`;
- a summary line with the count of open decisions and of unreviewed scientific assumptions;
- open decisions shown first.

## Texas A&M phase constitution: what the source states (owner's request)

**Searched:**
- `paper/main.tex` and `paper/supplementary.tex` of `ArroyaveLab/2026-mulukutla-hall-petch` at the pinned commit `11390ee516c1a17cacdde318b40d5d6889d4007f`, fetched 2026-10-05.
- Their SHA-256 equal the values recorded in step 4:
  - `main.tex`: `81fb864c…221836038e`;
  - `supplementary.tex`: `8dfe9731…d447461317`.
- Search terms (case-insensitive): single-phase, single phase, secondary/second phase, precipitate, XRD, X-ray, EBSD, recrystalli*, phase stability, design criteria, BCC, L1, sigma, intermetallic, homogeni*, and every mention of FCC.

**Passages about the lab's own alloys (verbatim):**

- `paper/main.tex` line 138 (introduction):
  > Hall-Petch parameters for FCC alloys are usually reported a few compositions at a time. Of the 630 alloys compiled by Borg et al., 27 single-phase FCC compositions carry grain size together with yield strength, drawn from 25 separate studies~\cite{Borg2020}. Six carry grain size, yield strength and hardness together. The 81 compositions measured here carry all three, under one processing route and one characterization protocol. This is the largest such set reported for single-phase FCC multi-principal element alloys, and it lets composition, processing and grain size be separated without correcting across studies.

- `paper/main.tex` line 173 (dataset), from its last three sentences:
  > The BB campaign contributes 35 candidates from batches BBA, BBB, and BBC, including 34 with YS. It explored composition under an FCC phase stability constraint while holding processing fixed. The complete BB-campaign synthesis and specimen preparation workflow is documented in Ref.~\cite{Mulukutla2026BRAVE}.

  The line opens with "The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system." (step 4's citation for phase class FCC).

- `paper/main.tex` line 175:
  > Candidate alloys were iteratively selected from an FCC-constrained, manufacturable design space with the models updated after each iteration using the newly acquired data.

- `paper/main.tex` line 177:
  > Overall, both campaigns used the same high level production route: high-purity elemental feedstock was vacuum arc melted, homogenized, cold rolled, recrystallized, and quenched. Energy-dispersive X-ray spectroscopy (EDS) and X-ray diffraction were used to check realized chemistry and phase constitution, while electron microscopy and EBSD documented the microstructure.

- `paper/supplementary.tex` line 61:
  > It explored the Al--Co--Cr--Cu--Fe--Mn--Ni--V system under an FCC phase-stability constraint while holding processing fixed.

- `paper/supplementary.tex` line 65:
  > Both campaigns followed the same high-level route of vacuum-arc melting from high-purity elements, homogenization, cold rolling, recrystallization, and quenching. EDS and XRD checked realized chemistry and phase constitution; SEM and EBSD documented the microstructure; and quasistatic tensile and Vickers indentation measurements supplied YS and HV.

- `paper/supplementary.tex` line 367 (a limitation of a strength model, not a statement about the samples):
  > Approximated elastic properties, calibration transfer, phase or local-order effects, and the subtraction used to define experimental friction stress can all contribute.

Other hits concern the literature (Borg et al.'s single-phase FCC records, `supplementary.tex` lines 461 and 465; the Table S12 caption on the Al₀.₃ alloys, line 439) or acknowledgements (line 597). No hit for secondary phase, precipitate (in the lab's alloys), sigma, intermetallic or L1₂.

**Does any amount to an explicit statement that the 94 conditions are single-phase? My reading: no.** The decision is the owner's; nothing was assigned.
- The closest is `main.tex` line 138. It calls "the 81 compositions measured here" "the largest such set reported for single-phase FCC multi-principal element alloys", which implies that the authors regard their alloys as single-phase FCC. But:
  - it is a comparative sentence in the introduction, not a methods or results statement;
  - it says 81 compositions, while the spreadsheet has 82 distinct compositions (step 1).
- Lines 173/175 and supplementary line 61 state a design **constraint** (FCC phase stability), not an observed result.
- Line 177 and supplementary line 65 say XRD and EDS **checked** phase constitution, without stating the outcome.

The question was left open in the first build.

## The owner's decision on the Texas A&M microstructure (2026-10-05)

**Decision:** the Texas A&M microstructure is "single-phase FCC", status "assigned by decision" (owner). Entry `tamu_microstructure` changed from open to in force:
- **Evidence, each with file and line (verbatim, in the entry):**
  - `main.tex` line 138: the authors describe their measured compositions as single-phase FCC;
  - the FCC design constraint: `main.tex` line 173 and `supplementary.tex` line 61 (BB campaign), and `main.tex` line 175 (CB campaign);
  - the XRD phase check: `main.tex` line 177 and `supplementary.tex` line 65.
- **Notes in the entry:**
  - the paper says 81 compositions and the spreadsheet has 82;
  - no passage states the result of the XRD check;
  - not reviewed by an expert.
- **Applied:** not yet, step 6. Today the adapter still reports the microstructure as not reported.
- **Sensitivity analysis:** the source-only analysis (reported values and values assigned from source only) shows the result without these records.
- **History:** "not reported: the source does not state the phases present per record (open decision)", 2026-10-05.

Register and summary only; no code applies it. With this, the register has no open decision, and the page's summary line reads "0 open decisions".

**MPEA microstructure** (computed from the adapter output, scratchpad script; nothing committed):
- All **77** reference records have microstructure exactly `FCC`.
- Among the 237 rows with a grain size:

| Microstructure | Rows |
|---|---|
| `FCC` | 107 |
| `BCC` | 36 |
| `FCC+Sec.` | 23 |
| (blank) | 9 |
| `FCC+HCP` | 8 |
| `BCC+FCC` | 6 |
| `BCC+B2`, `BCC+Sec.`, `Other` | 5 each |
| `FCC+BCC`, `B2+BCC`, `FCC+B2`, `BCC+Laves+Sec.` | 4 each |
| `BCC+Laves`, `FCC+BCC+Sec.` | 3 each |
| `FCC+L12+Sec.`, `BCC+B2+Laves` | 2 each |
| `BCC+HCP`, `BCC+BCC+HCP`, `FCC+B2+Sec.`, `FCC+L12`, `FCC+L12+B2`, `FCC+FCC`, `B2` | 1 each |

## Tests (527, all passing; 58 new; no test from an earlier step changed)

`git diff main --stat -- tests/` shows only the new `tests/test_assumptions.py`.

| Group | Tests |
|---|---|
| Schema | The file validates. Every category has entries, and keys are unique. The eight decisions are present: decided by the owner on 2026-10-05, not reviewed, applied as stated (c applied, the others not yet, at their steps). The owner's wording is checked (assigned by decision; rounded compositions identical, with no "within"; min(\|a\|, \|b\|) and "not final"; g's statement and its three notes; p < 0.05). The Texas A&M microstructure decision is recorded as decided (in force, owner, 2026-10-05, not reviewed, step 6, the six citations, the three notes, the sensitivity analysis, the open-decision history), and no decision is open. An open decision (a fixture, since the register has none) validates, and is refused if it carries a value or a decision. |
| Validator | 25 malformed cases, each refused with its message: missing or unknown field, bad key, category, state, blank text, empty evidence, bad dates, review status, a name without a review, accepted or disputed without a name or date, "applied: yes" with no setting or without `settings`, bad status, step outside 5–12, history out of order or after the decision, open/in-force inconsistencies. Also duplicate keys, an empty register, and an open decision (fixture) without `pending` or with a past step. |
| **Settings in code** | **Every "applied: yes" entry's settings resolve, and every `equals` matches the code** (25 entries). The values compared are spot-checked. 11 references to nothing are refused (missing constant, module, mapping key or parameter; a parameter without a default; a missing or partial SQL name; a wrong Dockerfile text; a path outside the repository; a missing file; an unknown kind). A wrong value and a missing setting are reported with the key. JSON terms are used for sets and tuples. |
| Page | Login is required for `/assumptions`, the filter URL and `/assumptions/`. Headings are in category order, every entry appears in its section, in register order. With an open decision added (fixture register), "Open decisions" comes first, holds only that entry, shows "Not decided" and the badge, and the summary counts it. Summary counts on the real register: 0 open decisions, 20 unreviewed scientific entries. The unreviewed-scientific mark is on exactly the right entries (with a fixture register where one scientific entry is reviewed). The filter shows exactly the not-reviewed entries (fixture with one accepted and one disputed entry). A row expands to reason, evidence, history, notes and sensitivity, and shows named settings or the step. The only form is sign-out, there is no input, and POST/PUT/PATCH/DELETE give 405. The service refuses an invalid register. The home page links to the page. |

### Tests changed after the owner's microstructure decision (none weakened)

The register no longer has an open decision, so three tests that used the real open entry now use a fixture:
- `test_open_decisions_have_no_value_in_force` asserted that `tamu_microstructure` was the one open entry. It is replaced by `test_the_microstructure_decision_is_recorded_and_no_decision_is_open`, which checks the decision and that no entry is open. The open-entry rules it covered are kept by the new `test_an_open_decision_has_no_value_in_force`, on a fixture open entry; that test also checks the refusal of an open entry carrying a value or a decision.
- `test_an_open_decision_needs_who_decides_and_by_when` builds its entry with the same fixture; its assertions are unchanged.
- `test_the_page_shows_every_entry_grouped_with_open_decisions_first` is renamed `test_the_page_shows_every_entry_grouped_by_category`. It expects the four category headings, because the register has no open decision; the section-by-section checks are unchanged. "Open decisions first" is now tested by the new `test_open_decisions_are_shown_first_when_there_are_any` (fixture register).
- `test_the_summary_line_counts_open_decisions_and_unreviewed_scientific_entries` now asserts "0 open decisions" explicitly.

### The safeguard tests fail when the safeguard is removed

Each change was made in a scratch copy of the working tree, and only `tests/test_assumptions.py` was run. The copy was then discarded.

| Change in the copy | Result |
|---|---|
| `WINDOW_SECONDS` 15 → 10 minutes | the settings test fails (and the reporting test, which uses that entry) |
| `PERCENT_SUM_TOLERANCE` renamed | the settings test fails |
| Texas A&M `grouping_unit` → `batch` | the settings test fails |
| Dockerfile `--workers 1` → `--workers 2` | the settings test fails |
| The validator accepts "applied: yes" with an empty settings list | the validator test for that case fails |
| The "Not reviewed by an expert" badge removed from the template | the mark test fails |
| The filter ignored | the filter test fails |

### Suite results
After the owner's microstructure decision (commit `b8837ee`):
```
$ pytest -q                              (Codespace, Python 3.14.2, `docker compose up -d db`)
527 passed in 61.29s
```
GitHub Actions, commit `b8837ee` (the last change to the register and tests): success; "Run the suite in the test image": 527 passed; "Check the default image holds no tests, docs or answers": runtime image OK.
https://github.com/kelawady/hypocurate/actions/runs/37263110672

First build (commit `8f7df59`), before that decision:
```
$ pytest -q                              525 passed in 73.41s
$ docker compose run --rm test           (the test image, rebuilt) 525 passed in 79.35s
```
The default (Render) image was built locally then: `scripts/check_runtime_image.py` on its `/app` said "runtime image OK", and inside the image `load_register()` read all 60 entries.
GitHub Actions, commit `8f7df59`: success, 525 passed, runtime image OK.
https://github.com/kelawady/hypocurate/actions/runs/37262162090

The step 1 answer-isolation scan (`test_no_row_answers_under_package`) passes with the register in the package. The register names the compression record by its origin key `MPEA_dataset.csv:row:139`, not in the answer file's wording.

## Deviations from the approved plan

1. **`base.html` gained a `main_attrs` block**, because `<main>` is 32 rem wide. The login, home and health pages render as before (their tests are unchanged and pass).
2. **The service refuses to start with an invalid register.** The plan did not say what happens then. A broken register therefore fails CI (the schema test) before any merge, and on Render a failed start keeps the previous version running.
3. **`markupsafe.escape`** is used in one page test to compare escaped text. markupsafe is already in the runtime lock (Jinja2 depends on it). No dependency change.
4. **Nine entry keys were renamed** from the plan (table above), and three entries were added while writing (above).

## PRD corrections and clarifications for the next PRD update

1. **PRD 5.10 (calibration assumptions):**
   - The scatter and per-paper shift are estimated by code from the frozen dataset's residuals after the freeze, by a method fixed at the rules lock (owner's decision g).
   - This replaces "never estimated from the real outcomes".
   - It is a safeguard change, reviewed before it is applied in step 7, against the alternative of reporting both ways.
2. **PRD 5.3 and 17 #4 (values disagree):** 2%, relative to the smaller value, for yield strength and grain size. The PRD recommended 15% for yield strength only. Which records are compared is open (repeat specimens are not conflicts).
3. **PRD 5.5 and 17 #7 (tag lists):** the owner's lists replace the recommendation.
4. **PRD 5.7 and 17 #9 (Texas A&M grouping unit):** one group, confirmed; "six batches" is a sensitivity analysis.
5. **PRD 5.8 and 17 #1 (fixed minimums):** 30, 5, 10 and 10, confirmed by the owner. The expert review is still pending.
6. **PRD 5.7 (verdict rule):** supported when p < α (strictly below).
7. **PRD 5.3 and 10 (assigned values):** two statuses, "assigned from source" and "assigned by decision", kept distinguishable. The reference plan names a sensitivity analysis that excludes decision-based assignments.
8. **PRD 10 (Texas A&M):** "82 single-phase FCC compositions" now rests on the owner's decision (assigned by decision), not on a statement in the source; the source says 81 compositions, and no passage states the XRD result. Step 4's correction 3 is resolved this way.
9. **PRD 10 (same alloy):** the rule is 0.1 at.% rounding with identical rounded compositions, with a 1 at.% sensitivity analysis. Step 4's correction 6 is resolved.
10. **PRD 9 and 15:** a read-only Assumptions page (step 4b), with the per-run "assumptions in force" panel at step 10; and CLAUDE.md "How we work", items 11 and 12.

## Open items

1. **Step 6** (each is in the register with its step):
   - apply decisions a, b, d, e, f and h, and the two assigned-value statuses;
   - the source-only sensitivity analysis;
   - the pairing for decision f (owner's approval);
   - apply the Texas A&M microstructure decision ("single-phase FCC", assigned by decision);
   - the room-temperature scope must accept the assigned band, with a test that the 21 Texas A&M records stay eligible.
2. **Before step 7:** recompute the reference numbers. Tension only removes `MPEA_dataset.csv:row:139` from the 77. The same-alloy rule is unchanged, so the alloy count changes only through that record. Update CLAUDE.md's "Reference numbers" when recomputed.
3. **Step 7:** the second-model review of decision g (both ways) before it is applied.
4. **Expert review:** every entry is "not reviewed". The page lists 20 scientific entries for Prof. El-Awady. A review is recorded in the register (status, name, date) in a reviewed merge.
5. **Carried, unchanged:** the step 4 open items (live registration after the owner's decisions; step 5 approved inputs; step 6 guards), and the step 3 step 7/9 requirements. The step 3 "p < vs ≤" item is closed by decision O.

## Questions for the reviewer

1. Is any assumption already in the code, the PRD or the summaries missing from the register, or stated more strongly than the code does?
2. Does the settings test ("applied: yes" names a setting that exists and holds the stated value) catch a default changed in code without the register? Which defaults would it miss (for example a literal that no entry names)?
3. Is refusing to start on an invalid register the right behaviour for the web service?
4. Is the page read-only in every way that matters (no form, no method other than GET, nothing written)?
