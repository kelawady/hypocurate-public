# Edit log: annotation_KE_v1.xlsx

| | |
|---|---|
| Original | `docs/sprint2/annotation_KE_v1.xlsx`, SHA-256 `e311a32d341ed15a79891a8aae8ab958ef2b9d7f4423e9f0d4ca48324a592a09`, kept unchanged |
| Loaded copy | `docs/sprint2/annotation_KE_v1_corrected.xlsx`, SHA-256 `cb59e726d36973a7dd2af0b2a606193a5854cc29ef6aa0672b7c2dad09b36b61` |
| Annotator | Codex (AI-assisted for KE): a reference-blind AI annotation reviewed by the owner, not a human key. Its minutes are AI elapsed time, not owner correction time. The human pass comes in the review week. |
| Decided by | Khalid El-Awady (owner), 2026-10-23 |
| Made by | Claude Code, on the owner's instruction |

## Corrections

| Sheet, row | Column | Before | After | Cause |
|---|---|---|---|---|
| Annotation, row 10 (10.1016/j.actamat.2018.12.012, the 711 MPa heterogeneous sample) | grain_size_value | (blank) | `0.2-20` (µm, unit unchanged) | **Annotation slip.** The row marks the grain size `range` but left the value blank, with the range in its ambiguity note ("Grain-size range ~0.2–20 µm …"). The template's Read me already says to write a range as the value, so this is a slip, not a gap in the template. The value is taken from the annotator's own note. |

## Changes made by saving the file, not edits

The spreadsheet library (openpyxl) writes two empty-text cells of the "Read me" sheet (lines 6 and 12, blank lines) as
empty cells. Nothing else differs: a cell-by-cell comparison of the Annotation sheet shows the one correction above
and no other change.

## Not changed

The owner asked for strain_rate 1.5e-4 /s on the Taylor & Francis rows (p. 83) if blank. All five already read
"1.5 × 10^-4 s^-1", so nothing was written.
