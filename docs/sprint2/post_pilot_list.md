# Post-pilot list (after the merge; the review week)

Items deferred from the pilot, each with its source. None of them blocks the merge.

## From ChatGPT's merge review of 2026-10-23 (B items)

1. **Make S1's information lineage testable.** S1 is defined by event authorship (`pilot_s1_definition`). Add a dependency and replay test showing that a machine-authored event in S1 has no input from a person's decision, and report it clearly.
2. **Separate historical execution time from import time.** The bundle replays model calls with load-time timestamps. Test the monthly totals across the load, and label imported spending explicitly, so the live ledger does not attribute historical calls to the wrong month.
3. **Test a disagreeing re-report through the whole pipeline.** The survivor is the compilation (`pilot_rereport_survivor`). Add an end-to-end case with a value disagreement that checks counting, retained values and the visible qualifier. The four accepted re-reports today all agree.

## Carried from earlier decisions

4. **Error reason on failed provider calls** (owner, 2026-10-23, approved as a safeguard change): store the HTTP status, the provider's error type and at most 200 characters of its message on the model_call row, with a test that a planted prompt string never appears there.
   - It needs a column on `model_call`. 0010 adds no column to an existing table, because the six reference dumps read every column. So it is a later migration.
5. **The survivor default should flip when the paper states the number and the compilation's value is a digitization** (owner, 2026-10-23; design open point in `pilot_rereport_survivor`).
6. **The full second-model review of the whole branch** (owner's condition (d) for the merge).
7. **The "per-document" cap is per document invocation.** Decide whether a cap per paper across invocations is wanted.
8. **Pipeline view (R13)**, cut from the pilot by the owner.
