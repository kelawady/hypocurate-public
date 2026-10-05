# Step 6 — second-model re-check (ChatGPT, 2026-10-06)

Re-check of `docs/reviews/step06_fix_packet.md` (branch `step-06-eligibility`). Saved verbatim as the owner gave it. The owner asked for the three remaining items to be fixed, each with a test that fails on the code before it (see `docs/reviews/step06_summary.md`).

---

Not ready to merge yet. The original matching and migration fixes are substantially addressed, but a concurrency gap remains, and other valid plan settings can bypass the new fixed rules.
Finding	Status	Assessment
1. Checks coverage	Partly closed	Sequential skipping, unfinished extraction and records added after Checks are now rejected. A race involving per-set flags remains below.
2. Sensitivity matching	Closed, subject to #1	Checks now recomputes matching flags under each set’s effective settings. The coarser-alloy example correctly retains two records rather than four. Inclusion receives categories and IDs, not compared outcomes. These are consequences of the single changed setting.
3. Source coverage and survivor order	Closed	The lock requires every chosen source in both settings; the final tie-breaker uses stable origin information. I found no remaining database-ID dependence in survivor selection.
4. Conflicts inside ambiguous groups	Closed	The three-source example now excludes A and C in possible_duplicates_separate, while permitting B if otherwise eligible. Primary still excludes the unresolved group.
5. Freeze fingerprint	Closed	Record IDs have been replaced with stable identities. The new same-database test addresses the previous test weakness. Different hypothesis-version IDs intentionally produce different plan fingerprints; that limitation is now stated.
6. Extraction constraint	Closed	Present string-valued fields and explicit false-on-NULL handling close the loophole. The original trigger checks remain intact.


The remaining issues, in seriousness order:
1. Concurrent operations can freeze a sensitivity set computed before its Checks flags existed.
set_flags() returns {} when Checks has not completed. Later, require_checks_cover() compares record identities and primary flags only.
An allowed interleaving is:
1. Freeze and Inclusion each read before Checks completes, obtaining empty per-set flags.
2. Checks commits: no primary flags, but duplicate flags for the coarser-alloy sensitivity.
3. Inclusion writes its stale decisions; the coverage check passes.
4. Freeze compares against those same stale decisions; it also passes.
Using the patched functions, the stale input retained four records, the completed Checks input retained two, and the coverage check accepted the stale view after Checks completed.
Fix: require completed Checks within the same transaction that reads Inclusion/freeze inputs. Missing required per-set flags should fail closed, rather than silently reuse primary flags. Add a controlled interleaving test.
2. The fixed rules can still be bypassed through other valid plan settings.
I reproduced two cases without changing the required eligibility-rule entries:
- Grouping changes duplicate identity. Set MPEA’s grouping to dataset while the other source remains paper. paper() then substitutes dataset:mpea for MPEA’s actual DOI. Identical cross-source records citing the same paper stop matching, and both enter primary. Statistical clustering should not erase known paper identity. Separate these concepts or reject inappropriate grouping overrides.
- Changing the outcome disables a physical-validity check. With ultimate_tensile_strength as the outcome, the UTS-below-YS check does not run. Records with UTS 399 and YS 400 receive no invalid flag and enter primary. That physical check must run independently of the selected outcome—or unsupported outcome choices must be rejected.
The new rule-map restrictions therefore do not yet establish the owner’s invariant.
3. Application-time validation misses duplicate rule entries.
fixed_rule_problems() converts entries into a dictionary, retaining the last duplicate. Actual rule lookup uses the first matching entry.
Prepending exact_duplicate → in_scope before the required correct entry passes the application-time check and admits both copies. Plan validation does reject this, so the normal lock path is protected; the claimed second enforcement point is not. Reject duplicate entries there too.
The unchanged reference numbers are expected: the reference sources have no shared measurements or invalid-value flags, the relevant coarse-alloy grouping is unchanged, and the default plan remains the same. These fixes principally affect constructed edge cases, sequencing and fingerprints.
I found no separate live-database safety blocker in migrations 0002/0003. Nevertheless, hold the step-6 merge until the concurrency and fixed-rule gaps are closed.
I reconstructed the patched modules and ran targeted reproductions; I did not independently rerun the reported 860-test PostgreSQL suite.
