# Controlled duplicate extract: construction and expected answers

**Test material. Never move any of this under `data/` or into the `hypocurate` package.** Tests check that no expected-outcome content exists there.

Keeping the answers here is a **convention, not a guarantee**. Until the access layer (step 5) restricts pipeline code to an approved list of input files, code with repository access could still open these files. It could also open the review documents in `docs/reviews/`, which contain the answers too. Both locations must stay outside that approved list.

| File | What it is |
|---|---|
| `build.py` | Builds `data/controlled_duplicates/extract.csv` and `truth.csv` from the frozen MPEA file. Deterministic. |
| `truth.csv` | The expected answer for each extract row. |

## The cases

All 16 source rows are among the records eligible under the reference plan, from eight papers. Two rows per case.

| Rows | Case | What was changed | Duplicate? | Primary analysis | Sensitivity |
|---|---|---|---|---|---|
| 1–2 | `exact_duplicate_verbatim` | nothing (byte-for-byte copy) | yes | counted once | none |
| 3–4 | `exact_duplicate_renamed_alloy` | formula written differently (`CoCrFeMnNi`, `Co4Cr1Ni4`); same atomic % | yes | counted once | none |
| 5–6 | `possible_duplicate_unknown_paper` | reference ID, DOI, year, title blanked | possible: flagged, kept, not removed | counted once | both counted separately |
| 7–8 | `conflict_value_differs` | yield strength × 1.3 | conflict: the same measurement reported with values beyond the tolerance | neither enters (decision C, owner 2026-10-05) | counted once by the survivor rule in `conflicts_survivor_value` |
| 9–10 | `not_duplicate_other_paper` | DOI → constructed `10.5555/hypocurate-test-…` | no | both enter | none |
| 11–12 | `not_duplicate_other_temperature` | 25 °C → −196 °C | no (conditions differ) | not eligible under a room-temperature plan | none |
| 13–14 | `missing_test_condition` | test temperature blanked | possible (conditions cannot be confirmed); kept, not removed | not eligible: scope not confirmed | included |
| 15–16 | `not_duplicate_other_test_type` | tension → compression | no (conditions known to differ; not a possible duplicate) | within scope under the reference plan (it sets no test-type rule): distinct measurements, both enter. Under a tension-only plan: excluded by the test-type rule | none |

**Missing paper vs missing test condition (PRD 5.3).**
- Rows 5–6: the paper is unknown but the conditions match. This is a possible duplicate that cannot be resolved.
- Rows 13–14: the paper is known but a test condition is missing, so the scope cannot be confirmed. The record stays out of the primary analysis and goes into the sensitivity analysis.

Every row is kept in the store and none is removed.

## Which record survives in the primary analysis

Owner's decision, 2026-10-04, refining PRD 5.3 (rule 1 in the owner's wording, restored in step 6; register entry 'duplicate_survivor_rule'):
1. Prefer the record that carries the original paper reference (DOI). A DOI identifies the cited paper, not where a record was extracted.
2. If both or neither do, take the first source in the fixed order: MPEA, Texas A&M, controlled extract.
3. Within one source, take the lowest row number.

For every duplicate and possible-duplicate row in this extract, the MPEA record survives:
- rows 1–4 and 13–14 by rule 2: both records carry the paper's DOI, and MPEA comes first in the fixed order (rows 13–14 are not eligible anyway);
- rows 5–6 by rule 1: only the MPEA record carries the paper's DOI.

Rows 7–8 are a conflict (decision C, owner 2026-10-05): neither enters the primary analysis; the sensitivity analysis `conflicts_survivor_value` counts each pair once, the MPEA record by rule 2.

No pair here lets a source other than MPEA survive. The step 6 tests add constructed records in which one does (`tests/test_eligibility.py`): the extract record wins by rule 1, and a Texas A&M record wins over an extract record by rule 2.

`truth.csv` gives the survivor and the reason for each row.

## Permitted test types (decided)

The owner decided on 2026-10-05 that the reference plan accepts tension tests only (register entry 'permitted_test_types'), which removes MPEA row 139 (a compression test) from its primary analysis. For rows 15–16 the column `handling_under_tension_only_plan` therefore gives the handling under today's reference plan; the columns `prd_5_3_class` and `primary_analysis` still describe the step 1 plan without a test-type rule. Aligning them is an open item for the owner (step 6 summary).

## Rebuilding

```
python tests/fixtures/controlled_duplicates/build.py
```
