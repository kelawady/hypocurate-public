# Midway submission: Plan panel, on-screen cleanup, README (review packet, 2026-11-02)

For the owner and a second-model review (ChatGPT). The review is advice; the tests decide.

Branches:
- `midway-screens` (from `pilot-live-record` 1f009ad): C in 9f99b5f, B in 139c1a8.
- `readme-course-staff` (from `midway-screens`): A, plus the public-copy scripts.

No migration, no `render.yaml` or workflow change, no safeguard touched. The panel reads the plan the run page already
read (`run_view.py`, `SELECT fingerprint, content FROM plan`) in the same read-only snapshot. No access-layer, eligibility,
checkpoint or validity code changed.

## C: leftover labels (9f99b5f)
- `home.html`: "Step 10a: the run pages. …" is replaced by a one-line pointer to Queries, Runs and Help. The Runs ·
  Assumptions · Health links stay. `test_assumptions.py:593` needs the `/assumptions` link.
- `run.html`: "· agent mode: {{ r.agent_mode }}" (shown as "agent mode: four roles") is removed from the header. The
  column (`run.agent_mode`, fixed to `'four_roles'`) and the workbook's "Agent mode" row stay (owner's answer: a
  factual record).
- `run.html`: the Commentary section ("No commentary: the Commentator is not built in sprint 1 (PRD 15, step 12).")
  is removed (owner's review). The run page never loads commentary. The workbook's commentary line stays.
- Not changed: "step 10a" mentions inside register notes and history on /assumptions (history is not rewritten), and
  code comments.

## B: the Plan panel (139c1a8)
- `run_view.plan_rows(plan, names)` builds nine rows: Population, Test conditions, Exclusions, Same alloy, Same
  record, Model, Test, Minimum evidence, Checks. Every value is read from the locked plan's own fields. The Hypothesis
  row comes first in the template: the stored claim, with code's question as tested under it.
- Rules code applies to every plan are written in code and say so:
  - the physically impossible values (`flags.invalid_values`);
  - records within one source are always separate;
  - cluster-robust standard errors with the small-sample correction and t on informative groups minus 1.
- Owner's answers applied:
  - the stored plan exactly, so "Same record" says conditions equal and the minimums include 10 residual degrees of
    freedom (Table 1 of report v0.10 differs here; the owner corrects it in v0.11);
  - grouping and the survivor order list only the run's sources;
  - a set about a source the run did not choose says "no Texas A&M records in this run, so identical to the main
    result" (owner's review: "not applicable" contradicted the sensitivity table, which shows the set as run);
  - the panel sits below the Results statement, or below the question as tested for a locked run not yet completed;
  - no panel before the rules lock.
- `SET_SOURCE = {"six_batches_as_groups": ("tamu_fcc", "Texas A&M")}` restates what `eligibility.settings` changes for that set. A
  test checks that the two agree.
- Glossary entry `plan`. Register entry `plan_panel_rows` (applied: `PLAN_PARTS`, `SET_SOURCE`, `NO_RECORDS_OF_SOURCE`).
- **For the owner:** "atomic percent (at.%)" is written out once on the run page, in the sensitivity table's set name
  (register `sensitivity_set_display_names`, test `test_atomic_percent_is_written_out_once_on_the_run_page`). The panel
  comes first, so its Checks row uses "at.%" only, and the test is unchanged. On a locked run that has not completed
  (no sensitivity table yet), "at.%" is therefore not written out on the page. Owner: leave as is.

Screenshots (local site, every model call to the stub provider, $0):
- `midway_screens/plan_panel_run11_shape.png`: run 11's shape. This is a fixed-plan run of Q-0010's claim on MPEA and
  the extracted records, on a throwaway copy of the development database; it froze 77 records, as run 11 did.
- `midway_screens/plan_panel_wide.png` and `plan_panel_phone.png`: the R9 rehearsal run 18 (MPEA, Texas A&M and the
  extracted records) on the scratch copy `hc_scratch_r9`.
- `midway_screens/home.png`: the home page.

The run-11-shaped screenshot found a defect the unit tests had missed: a run's source rows include the sources it did
not choose (search status `not_selected`), and the panel listed them. Fixed (the panel uses only the chosen sources),
with the web test `test_the_panel_lists_only_the_sources_the_run_chose`, which failed before the fix.

## Tests added (`tests/test_midway_screens.py`, 14)
- C:
  - the home page names no build step and keeps its links;
  - the run page has no commentary section;
  - the run page header has no agent mode;
  - the workbook still records it.
- B:
  - every row for the reference plan;
  - a planted plan, where every value changed from the profile's shows on the panel;
  - a rule the plan does not hold is not shown;
  - use what is available;
  - a band other than room temperature;
  - run 11's shape (pilot sources only, the Texas A&M set identical to the main result);
  - a run that chose only some sources lists only those (web test);
  - `SET_SOURCE` agrees with `eligibility.settings`;
  - the completed run shows the panel between the Results statement and the Analyst, with every row, the claim, the
    question as tested and the fingerprint;
  - no panel before the rules lock.
- Mutation checks (each caught by a test, then restored):
  - room temperature range taken from a constant instead of the plan;
  - grouping not filtered to the run's sources;
  - the panel removed from the template.

## A: README (branch `readme-course-staff`)
- Rewritten for course staff using the hosted site: access, reproducing Q-0010 with "Dispatch again (a new run)",
  what the run page shows, a short note on entering one's own claim, extraction results, code map, limits.
- The previous developer material moved unchanged to `docs/DEVELOPING.md` (the stale "Status" paragraph dropped).
- `tests/conftest.py` help text and two test docstrings now point to `docs/DEVELOPING.md`. No assertion changed.

## Open
- Answered by the owner from the live run 11 page: run 11 took about 1.7 minutes (18:32:54 to 18:34:33 UTC), and the
  extracted source shows as `extracted_pilot` in the per-source table and plot legend, "Extracted records (Sprint 2
  pilot)" in the Sources list. The owner checks the worker in Render.
- The whole suite result and GitHub suite time are reported with the push.
