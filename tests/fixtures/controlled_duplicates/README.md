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
| 7–8 | `not_duplicate_value_differs` | yield strength × 1.3 | no | both enter | none |
| 9–10 | `not_duplicate_other_paper` | DOI → constructed `10.5555/hypocurate-test-…` | no | both enter | none |
| 11–12 | `not_duplicate_other_temperature` | 25 °C → −196 °C | no (conditions differ) | not eligible under a room-temperature plan | none |
| 13–14 | `missing_test_condition` | test temperature blanked | possible (conditions cannot be confirmed); kept, not removed | not eligible: scope not confirmed | included |
| 15–16 | `not_duplicate_other_test_type` | tension → compression | no (conditions known to differ; not a possible duplicate) | within scope under the reference plan (it sets no test-type rule): distinct measurements, both enter. Under a tension-only plan: excluded by the test-type rule | none |

**Missing paper vs missing test condition (PRD 5.3).**
- Rows 5–6: the paper is unknown but the conditions match. This is a possible duplicate that cannot be resolved.
- Rows 13–14: the paper is known but a test condition is missing, so the scope cannot be confirmed. The record stays out of the primary analysis and goes into the sensitivity analysis.

Every row is kept in the store and none is removed.

## Which record survives in the primary analysis

Owner's decision, 2026-10-04, refining PRD 5.3:
1. Prefer the record that comes directly from the original paper. This is detected by the original paper's DOI on the record.
2. If both or neither do, take the first source in the fixed order: MPEA, Texas A&M, controlled extract.
3. Within one source, take the lowest row number.

For every duplicate and possible-duplicate row in this extract, the MPEA record survives:
- rows 1–4 and 13–14 by rule 2: both records carry the paper's DOI, and MPEA comes first in the fixed order (rows 13–14 are not eligible anyway);
- rows 5–6 by rule 1: only the MPEA record carries the paper's DOI.

No pair here lets a source other than MPEA survive. The behavioural tests in step 6 need one that does.

`truth.csv` gives the survivor and the reason for each row.

## Open question (owner)

The reference plan's 77 MPEA records include one compression test (MPEA row 139). The reference plan does not yet state its permitted test types, and membership in that result set must not define the rule. The plan must state them explicitly before eligibility is implemented in step 6. This is pending the owner's decision. Rows 15–16 give the expected handling both ways: under the reference plan as it stands (no test-type rule), and under a tension-only plan.

## Rebuilding

```
python tests/fixtures/controlled_duplicates/build.py
```
