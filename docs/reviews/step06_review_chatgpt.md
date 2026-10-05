# Step 6 — second-model review (ChatGPT, 2026-10-06)

Review of `docs/reviews/step06_review_packet.md` (branch `step-06-eligibility`, code commit `b11e7c8`). Saved verbatim as the owner gave it. The owner accepted all six findings on 2026-10-06, with a decision on conflicts and exact duplicates (see `docs/reviews/step06_summary.md`).

---

There are serious correctness gaps. I would hold step 6. These are ordinary sequencing and data-handling mistakes within the agreed threat model—not hostile-code scenarios.
Findings, in seriousness order:
1. Checks can be skipped or become stale, and the freeze can still accept the result.
   decide_run() does not require a completed Checks stage covering the current records. freeze_dataset() recomputes decisions from the stored flags, without establishing that those flags cover every record.
   Two ordinary mistakes therefore matter:
   - Store records → skip Checks → decide → freeze.
   - Store source A → run Checks → store source B → decide → freeze.
   Both can produce internally consistent decisions based on missing flags. The second case also cannot simply rerun Checks because it is once-only. Comparing record IDs between each individual read and write does not close this gap.
   Fix: require extraction to finish before Checks, bind the completed Checks result to the exact record collection, and verify that binding before Inclusion and freeze. Test both sequences above with actual conflicting records.
2. The coarser-alloy sensitivity does not recompute duplicates under its changed alloy definition.
   same_alloy_1_at_pct changes Settings.decimals, but all_sets() reuses flags computed under the primary plan’s precision.
   I reproduced this with two compositions—Co50.06/Ni49.94 and Co50.04/Ni49.96—each represented at two grain sizes across two sources. The sensitivity retains all four records. Recomputing duplicate flags at its stated precision correctly counts only two.
   Fix: compute the relevant matching flags under each sensitivity’s effective settings, then apply the remaining rules unchanged. Inclusion can remain outcome-blind; Checks should supply those flags.
   The existing sensitivity test misses this and actually assumes that coarser grouping can change only single_grain_size versus in_scope.
3. An incomplete survivor order makes the selected record depend on database insertion order.
   Plan validation accepts an empty or incomplete survivor_source_order. Unlisted sources share the same priority; equal DOI status and row number then fall through to the database record ID.
   I reproduced a survivor switching from MPEA to the extract solely by swapping insertion IDs, with the same plan and source records.
   The validator likewise accepts empty/incomplete grouping, leaving some records without a group.
   Fix: at the rules lock, require the ordering and grouping settings to cover every selected source. Use stable source/origin identity for any final tie-breaker. Tests should vary insertion order and omit one selected source from each setting.
4. Ambiguous groups can hide a definite conflict from the sensitivity rules.
   Consider three sources:
   - A reports 400, with a DOI.
   - B reports 400, without a DOI.
   - C reports 440, with A’s DOI.
   A–C is a definite conflict; A–B is a possible duplicate; B–C does not link. The component becomes only possible_duplicate / several candidates. Its conflict information is absent from Inclusion’s input.
   The primary set correctly excludes the group. But possible_duplicates_separate then admits both conflicting values. I reproduced this with another grain size present.
   That contradicts the promise that this sensitivity changes unresolved-identity handling while leaving conflict handling unchanged. Preserve the conflict information when labelling a component ambiguous, and test the resulting sets—not just the flag label.
5. The freeze fingerprint is not reproducible independently of database IDs.
   The fingerprint includes record IDs in both sets and rules. Identical records and the same plan produce different fingerprints when the record sequence starts elsewhere. I confirmed this using the packet’s fingerprint calculation.
   The existing test creates two databases from the same template and follows identical insertion steps, reproducing the same IDs rather than testing independence from them.
   Fix: fingerprint stable record identities—source-version fingerprint, origin and item index—plus content and decisions. Keep database IDs separately for lookup. Test two identical runs after unrelated inserts or in the same database.
6. Migration 0003’s extraction constraint accepts a missing method.
   This passes the new shape check:
   {"name": "mpea_layout", "version": "1"}
   The missing method makes its comparison evaluate to SQL NULL; PostgreSQL accepts a CHECK yielding NULL. The trigger rejects only a NULL extraction column. Numeric/object name and version values can also pass because ->> converts them to text. PostgreSQL constraint semantics, JSON extraction semantics.
   Fix: require the necessary keys and JSON string types, and make the predicate explicitly true. Add missing-method, null-method and wrong-type tests.
   Otherwise, the replaced trigger preserves the earlier checks, and the migration transaction/rollback tests look appropriate. Migration 0002’s intentional no-op downgrade is accurately described.
On the remaining questions:
- Outcome blindness: I found no raw outcome value in Inclusion’s projected input or relationship-fitting logic in Checks. Outcome-derived flags and availability statuses deliberately influence eligibility. That qualification is accurate. “Only pairwise rules” is slightly imprecise: pairwise comparisons feed whole-component classification.
- Locked settings and sensitivity names: encoding a fixed change in a named sensitivity is acceptable; duplicating every constant into the plan is unnecessary. Its meaning must remain stable or be versioned. The broad “every setting comes only from the plan” claim needs narrowing because fixed policies such as flags.VALUE_STATUSES still live in code.
- Conflict policy: PRD 5.3 permits pre-lock overrides, and the implementation explicitly tests mapping conflicts to in_scope. Consequently, “neither conflict record enters primary” is currently a default, not an invariant. Clarify whether the owner’s later decision was intended to remove that override.
- Constructed-data guard: the three checks cover the registered constructed source under the agreed code-only approach. I found no additional blocker there; unknown source definitions should eventually fail closed.
- Reference numbers: the counts hang together: 76 + 21 = 97 records; 13 + 9 = 22 alloys; 19 + 1 = 20 groups; residual df = 97 − 22 − 1 = 74. The other table rows are similarly consistent. Three eligible Texas A&M batches explain 22 pooled sensitivity groups. The fitting script matches the specified OLS, clustered standard-error correction and one-sided t calculation. Label “±” explicitly as one standard error, not a confidence interval. statsmodels documentation
- Scope: the test-side statistical recomputation is appropriate verification, not problematic step-7 implementation creep.
I ran targeted extracted-code reproductions, not the reported 816-test PostgreSQL suite or the numerical fits. The sequencing, sensitivity and determinism gaps need fixing before sign-off.
