I would hold the merge. The main freeze and lifecycle fixes are present, but the locking protocol and source-version fingerprint still have substantive gaps.
This is a review of the packet’s code and tests. I did not independently rerun the PostgreSQL suite.
Original finding	Status	Assessment
1. Locking protocol	Partly closed	Checkpoint races are addressed, but a parent/child deadlock path remains.
2. Exact primary set at freeze	Closed	Every extracted record must have a decision; primary membership must equal the eligible records.
3. Lifecycle and post-completion writes	Partly closed	Core outcome, verdict, results and record sets are protected. A Commentator stage’s role can still change.
4. Source sealing and fingerprint	Partly closed	Files and interpretation settings are sealed, but fingerprint serialization and version uniqueness need correction.
5. Validity-check wording	Closed	The packet now distinguishes necessary database checks from the full validation deferred to step 7.
6. Search coverage	Closed	Separate categories come from the run’s own source rows; the misleading collapsed label is gone.
7. Costs	Partly closed	Precision and reservation contracts are improved, but non-finite monetary values remain accepted.


Remaining findings, in seriousness order:
1. The lock order excludes implicit child-row locks.
In hc_stage_result_update, hc_model_call_update and similar update triggers, PostgreSQL has already locked the target child row before the trigger requests the run lock. This permits:
1. Transaction A locks the run.
2. Transaction B updates a child row, locks that row, then waits for A’s run lock.
3. A updates the same child row and waits for B.
That is a deadlock. PostgreSQL aborts one transaction, so this is an availability/retry problem rather than silent corruption. Nevertheless, the claimed complete lock order is not established. PostgreSQL locking documentation
The two-connection tests demonstrate the particular checkpoint races they exercise. They do not exercise this second write by A while B is waiting.
Fix: require supported write paths to acquire the parent lock before issuing child updates, and test that interleaving. A child’s row trigger alone cannot establish that order. Document deadlock retries for any remaining supported multi-row transaction patterns.
2. Source fingerprints have two distinct problems.
- Ambiguous serialization: hc_files_fingerprint concatenates checksum, filename and newline, but filenames may themselves contain newlines. Two files named a.csv and b.csv can produce exactly the same serialized input as one file whose filename embeds the newline and the second checksum/path. I independently checked this construction. This is an encoding collision, not a SHA-256 weakness. Reject line breaks in paths or use an unambiguous encoding.
- Interpretation-only revisions cannot be sealed: UNIQUE(source_id, fingerprint) prevents a new version containing the same files but corrected interpretation settings. The new interpretation-settings test creates an unsealed replacement, so it misses this failure.
Keep a file-content digest if useful, but let version identity distinguish interpretation settings. Add a test that successfully seals the same files under revised settings.
3. Costs accept NaN and positive infinity.
Unbounded PostgreSQL NUMERIC supports these values. The current max_cost > 0 and nonnegative-cost checks admit them; PostgreSQL orders numeric NaN above ordinary numbers. They can contaminate cost totals and budget calculations, and finished calls cannot subsequently be corrected. PostgreSQL numeric documentation
Require finite max_cost and finite non-null cost, with rejection tests for both special values. The remaining step-9 requirements—committing reservations before requests and atomically checking budgets—are now stated appropriately.
4. A completed run’s Commentator stage can be relabelled.
hc_stage_result_update freezes the stage name but not role. A permitted Commentator stage can subsequently be updated to role = 'planner', including when finishing it.
This does not reopen the verdict or record sets, but it breaks the stated post-completion role restriction and audit attribution. Freeze the role and test this update explicitly.
The replaced-test list does not reveal a still-required behaviour that was simply discarded. The removed aggregate coverage expectations and obsolete setup paths have legitimate replacements. The missing coverage is principally the deadlock interleaving, ambiguous filenames, sealing interpretation-only revisions, non-finite costs and stage-role updates.
Merge decision: fix these before the first live migration, then rerun the PostgreSQL suite. I found no additional blocker in the migration’s transactional structure. The up/down/up test establishes reproducible schema creation; it does not establish these behavioural guarantees.
