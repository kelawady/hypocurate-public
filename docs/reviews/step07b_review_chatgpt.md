I found no serious defect or merge blocker. The safeguards implement the owner’s decisions. Three non-blocking observations, in order of importance:
1. Simulation seeds unnecessarily couple unrelated analyses.
   File: pipeline/calibration.py, seed(); freeze fingerprint construction.
   The packet supplies the example: adding one descriptive set changes every existing calibration draw, although those analyses have identical data and settings. This does not change the verdict or break reproducibility of an unchanged run, but it makes comparisons unnecessarily noisy.
   Prefer an analysis-specific fingerprint covering its stable records/design, relevant simulation settings and calibration method. The set’s name alone is insufficient. Keep the complete run fingerprint for provenance. This can wait.
   At an 8% rejection rate, 2,000 simulations give an approximate 95% Monte Carlo margin of ±1.2 percentage points. That is adequate for a coarse diagnostic, not precise comparisons between 7.25%, 7.85% and 8.85%. About 10,000 simulations reduces that margin to ±0.53 points. The observed changes are consistent with simulation noise; the table does not prove noise is their only explanation.
2. “Most influential paper” needs a precise display description.
   Files: pipeline/eligibility.py, most_influential(); assumptions.json.
   The code selects the largest share of within-alloy predictor contrast, not necessarily the paper whose removal changes the estimated slope most. A paper with substantial predictor contrast but outcomes close to the fitted relationship illustrates the distinction. Also, under dataset or batch grouping, the selected unit need not be one paper.
   Keep the internal key, but display “without the group with the largest share of slope information,” identifying whether that group is a paper, dataset or batch.
3. One modified assertion partly derives its expectation from the result being checked.
   File: tests/test_controlled_duplicates_handling.py, test_the_sensitivity_handling_is_the_answer_files().
   The new branch permits a primary member to become most_influential_paper whenever the actual result says so. That assertion alone would accept removing the wrong member. Other tests substantially compensate: they check whole-group removal and independently identify the maximum on the reference data. When next editing this test, derive the expected removed members independently rather than consulting the actual rule.
On the safeguards you asked about:
- Rule 5 is correctly positioned. Earlier basic exclusions retain their reasons; an ungrouped record cannot become the duplicate survivor or supply the extra grain size that makes an alloy eligible. The source-priority counterexample passes: the grouped twin survives even when source order prefers the ungrouped record. Grouping is evaluated separately for each set. Retaining definite duplicate/conflict relationships through excluded records remains appropriate.
- Freeze invariant 7 checks membership directly. It inspects the primary members through group_in, without trusting their eligibility rule or calling has_group. Sharing the definition of a group is appropriate; this is independent enforcement, not an independently implemented grouping algorithm.
- The new set is deterministic and makes exactly one membership change. Selection reads no outcome values and uses stable source evidence rather than database ids. It removes every primary member of the chosen group without rerunning eligibility. Any subsequent loss of an alloy’s usable contrast is correctly reported by the fit. The verdict still comes solely from the pooled result.
- The information calculation is consistent. Selection and statistics share _information, with matching transformation, alloy filtering and centring. The independent formula and consistency checks passed.
- The answer-file changes are justified. Rows 5–6 now reflect the owner’s exclusion decision. Changing identity-test fixtures to dataset grouping preserves their original purpose; the statistics backstop remains tested. Apart from the local assertion weakness above, I found no material protection lost.
I reconstructed the relevant packet changes and ran 23 focused test cases plus a direct freeze-invariant check successfully. I did not independently rerun the database integration suite, reference-data comparison or reported 1,186-test suite. The local numerical environment reported the same NumPy/SciPy compatibility warning as before.
Safe to merge.


7:28 AM
