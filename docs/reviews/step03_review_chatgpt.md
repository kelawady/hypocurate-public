I would not sign off step 3 yet. The migration machinery looks sound, but several database safeguards permit states the PRD forbids. These are ordinary application writes—not cases requiring someone to disable triggers.
1. High — Concurrent transactions can defeat the dataset freeze.
   The triggers check for a snapshot without taking a shared serialization lock. For example:
   - Transaction A inserts another primary-set member, passes the “not frozen” check, and remains uncommitted.
   - Transaction B freezes the run, counting only committed members, and commits.
   - A commits. The frozen set now contains an additional record.
   Similar races exist between chosen-source changes and submission, and between dispatch metadata insertion and starting a run. PostgreSQL’s default isolation does not make these cross-table checks atomic. Use a consistent per-run/per-version locking protocol before checking or changing state, and add two-connection tests. [Freeze triggers (line 2053)](local-path); PostgreSQL isolation rules.
2. High — The primary set can silently omit eligible records.
   Freeze validates the size of the set supplied, not its completeness. Mark ten records eligible, put three into primary, and freeze with n_records=3: the checks permit it. Records can also remain undecided.
   That leaves an outcome-driven selection path despite immutable eligibility decisions. At freeze, require every collected record to have a decision and the primary membership to equal the eligible record set. Sensitivity membership remains separately defined. The [freeze function (line 2075)](local-path) needs this invariant.
3. High — Checkpoint ordering and finality are incomplete.
   Several sequential bypasses remain:
   - record insertion requires a running run but no locked plan, allowing extraction before rules lock.
   - A pending run_source can become searched after the run completes, changing its derived “nothing found” result.
   - A run-level no_dataset_frozen calibration can be inserted first, followed by a dataset freeze, leaving contradictory permanent records.
   - Eligibility, set and flag operations generally check the snapshot but not whether the run has already failed or completed.
   Enforce the permitted lifecycle on both sides of these relationships. “No snapshot exists” is not equivalent to “curation is still allowed.”
4. High — A source version does not actually freeze its inputs.
   Existing source_file rows are immutable, but additional files can be inserted into an already-used version. Meanwhile, source.grouping_unit, data_kind and other interpretation metadata remain mutable outside the version.
   A run can therefore retain the same source-version identifier while its available files or grouping interpretation change. Seal file membership before a version is used, and snapshot interpretation-critical metadata into the version. Operational settings such as enabled/disabled can remain mutable. See [source models (line 557)](local-path).
5. Medium — The database overstates what its statistical validity checks establish.
   check1_passed = (n_alloys >= 1) is not PRD 5.7’s “an alloy measured at two distinct grain sizes.” A one-record set can claim a fitted coefficient. Only n_records is checked against membership; alloy and group counts are accepted from the caller.
   Add necessary count-consistency constraints now, and explicitly assign distinct-grain-size/group validation to the later deterministic analysis code. Do not describe the present CHECKs as enforcing the full validity rules.
   The exploratory trigger does match the documented owner clarification. Verdict presence is constrained correctly, but verdict agreement with the pooled result remains unenforced, as the summary acknowledges. Keep that explicit as a step-7 acceptance requirement.
6. Medium — “Reported negative” overstates mixed search results, and historical coverage can change.
   One negative report plus missing evidence elsewhere should not collapse into an unqualified run-level “reported negative.” Preserve both categories, for example: “Insufficient evidence; negative findings reported in source A.”
   Separately, not_searched_sources queries the current source registry. Registering a source tomorrow changes yesterday’s run summary. Derive historical coverage from the run’s dispatch-time source inventory. See [view definition (line 2319)](local-path).
7. Medium — Cost sums are correct for stored rows, but “cannot under-count spending” is not established.
   The views correctly include charged failures and reserve max_cost for unreported calls. The one-time finishing trigger also looks correct: concurrent updates to the same call serialize, and the second finish is rejected.
   Remaining limits:
   - NUMERIC(12,6) rounds each cost and reservation; sufficiently small positive amounts round to zero. Use adequate precision and round reservations conservatively. PostgreSQL numeric behavior
   - A stated bound of zero or an underestimated bound is accepted. The later caller must establish a genuine upper bound.
   - The reservation must commit before the external request. Otherwise a rollback can erase a charged call.
   - Monthly totals use caller-supplied started_at; define month-boundary attribution and prevent arbitrary backdating.
   - Views alone cannot prevent two callers from spending the same remaining budget. Atomic reservation belongs with the later spending-cap implementation.
Migration safety: the single transaction and transaction-level advisory lock are appropriate. I see no half-applied-schema path in this migration. The injected-failure test meaningfully tests rollback, and up/down/up tests reproducibility of the empty schema. However, a successful migration is not undone if application startup subsequently fails. Backward compatibility remains necessary.
The proof also has limits: repeating the same incorrect schema twice still passes. CHECK comparison verifies names, not predicate equivalence; expected trigger names come from the migration itself. This is useful drift coverage, not independent proof of the rules.
Tests needing attention: add concurrent checkpoint tests, omitted-eligible-record tests, pre-lock extraction tests, post-completion child-write tests and source-version sealing tests. The duplicate test manually supplies the correct eligibility and membership; it demonstrates storage capability, not duplicate handling. That algorithm can properly wait until its implementation step.
I found no obvious TRUNCATE escape in the protected tables and no deferred foreign keys in the migration. The model-call identity comparisons use non-nullable fields, so the suggested NULL-comparison bypass does not apply there.
Scope: no meaningful scope creep. Access masking, duplicate detection and statistical computation can remain later steps. Structural completeness, immutable source snapshots and race-safe checkpoint transitions should be fixed in the database now.
I verified 22 fully embedded files. PostgreSQL was unavailable locally, so these findings are based on code inspection; I did not independently execute the 316-test suite or the proposed two-session reproductions.
