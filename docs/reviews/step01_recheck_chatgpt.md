Almost ready. I would make one small fixture correction before signing off step 1.
Finding	Status	Assessment
1. Answer leakage	Partly closed	The answer table and builder pointer are removed from data/; the builder and truth file now live under tests. However, content scans do not prevent pipeline code with repository access from opening those files—or the review documents containing answers. Actual access enforcement remains a step-5 requirement, appropriately deferred.
2. Freeze protection	Closed	The fixed six-file inventory and independently pinned manifest hash close the identified gaps. With the tests unchanged, altering a frozen file, extract or manifest fails a check, including coordinated data-and-manifest edits.
3. Duplicate cases and survivor	Partly closed	The missing-condition case has the correct primary/sensitivity treatment. Known-different test types correctly count as nonduplicates. Survivor identities are now explicit. One contradictory classification remains, detailed below.
4. Review checklist	Closed for this review	The checklist exists and covers the required questions. Its stated owner approval is still pending administratively.


The remaining correction: rows 15–16 have prd_5_3_class = "Incompatible measurements: outside the plan's scope" but primary_analysis = "both enter under the reference plan...". Those statements cannot both describe the same plan. Section 5.3 excludes out-of-scope measurements.
Keep the nonduplicate classification and, if the reference plan permits both test types, label these records as within-scope, distinct measurements. Alternatively, explicitly test a tension-only plan and expect exclusion. Do not silently change the reference baseline. The contradiction appears in the [case definition (line 333)](local-path) and committed truth file.
Two points to carry forward, without expanding step 1:
- The survivor results fit the documented refinement, but “carries the original paper’s DOI” is not equivalent to “comes directly from the original paper.” Align that wording with PRD 5.3 before implementation. All current pairs select MPEA; later behavioral tests should include a case where another source wins.
- The packet reports a compression measurement in the reference set. Make the reference plan’s permitted test types explicit before implementing eligibility; membership in an existing result set should not itself define the rule.
Sign-off: correct the contradictory fixture label and its expected test, then I see no remaining step-1 blocker. Runtime answer isolation belongs to step 5; stop claiming it is already guaranteed merely by directory placement.
I independently verified all ten embedded files’ hashes and sizes, plus the manifest, extract and truth pins. I could not rerun the full reported 91-test suite because the upstream data files are omitted.
