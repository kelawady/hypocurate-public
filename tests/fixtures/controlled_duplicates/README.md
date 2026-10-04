# Controlled duplicate extract: construction and expected answers

**Test material. Never move any of this under `data/` or into the `hypocurate` package.** The pipeline must not be able to read the expected answers. Tests check that no expected-outcome content exists there.

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
| 15–16 | `not_duplicate_other_test_type` | tension → compression | no (conditions known to differ; not a possible duplicate) | both enter under the reference plan (it sets no test-type rule) | none |

**Missing paper vs missing test condition (PRD 5.3).**
- Rows 5–6: the paper is unknown but the conditions match. This is a possible duplicate that cannot be resolved.
- Rows 13–14: the paper is known but a test condition is missing, so the scope cannot be confirmed. The record stays out of the primary analysis and goes into the sensitivity analysis.

Every row is kept in the store and none is removed.

## Which record survives in the primary analysis

Owner's decision, 2026-10-04, refining PRD 5.3:
1. Prefer the record that carries the original paper reference (DOI).
2. If both or neither do, take the first source in the fixed order: MPEA, Texas A&M, controlled extract.
3. Within one source, take the lowest row number.

For every duplicate and possible-duplicate row in this extract, the MPEA record survives:
- rows 1–4 and 13–14 by rule 2 (rows 13–14 are not eligible anyway);
- rows 5–6 by rule 1.

`truth.csv` gives the survivor and the reason for each row.

## Open question (owner)

The reference plan's 77 MPEA records include one compression test (MPEA row 139), so the reference plan sets no test-type rule. Rows 15–16 are stated relative to that plan.

## Rebuilding

```
python tests/fixtures/controlled_duplicates/build.py
```
