# Controlled duplicate extract

**Constructed test data.** These 12 records are built from the frozen MPEA dataset (`data/sources/mpea/MPEA_dataset.csv`) by `scripts/build_controlled_duplicates.py`. They exist only to test duplicate detection (PRD Sections 5.3, 10 and 14.1). They are never pooled into a real analysis or a reference run.

The two sprint sources share no measurements, so this extract overlaps the MPEA dataset in a known way. The truth is known by construction.

## Format

The same columns as the MPEA dataset, with the header copied verbatim. Each row is one MPEA record, either copied unchanged or with the listed columns changed.

## The cases

All source rows are among the records eligible under the reference plan, from eight papers.

| Rows | Case | What was changed | Duplicate? |
|---|---|---|---|
| 1–2 | Exact duplicate, verbatim | nothing (byte-for-byte copy) | yes |
| 3–4 | Exact duplicate, renamed alloy | formula written differently (`CoCrFeMnNi`, `Co4Cr1Ni4`); same composition in atomic percent | yes |
| 5–6 | Paper unknown | reference ID, DOI, year and title blanked | possible: flagged, kept, not removed |
| 7–8 | Same paper, alloy and grain size; value differs | yield strength × 1.3 | no |
| 9–10 | Same alloy, grain size and value; other paper | DOI set to a constructed `10.5555/hypocurate-test-…` reference | no |
| 11–12 | Same everything except test temperature | 25 °C → −196 °C | no (conditions differ) |

Two records count as duplicates only if they come from the same original paper and match on alloy, grain size, value and test conditions (PRD 5.3). Matching alloy and grain size alone is not enough.

## Where the answers are

The expected result for each row is kept with the tests, outside `data/` and outside the `hypocurate` package, so no part of the pipeline can read it. Nothing under `data/` names its location; a test checks that.

## Rebuilding

```
python scripts/build_controlled_duplicates.py
```

This writes the same bytes every time. A test checks that rebuilding gives exactly the committed extract and answer file, and the extract's fingerprint is in `data/manifest.json`.
