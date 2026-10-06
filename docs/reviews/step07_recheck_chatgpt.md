# Step 7 — second-model re-check (ChatGPT), 2026-10-06

Saved verbatim as pasted by the owner.

The original cases are closed, but I cannot sign off yet. The informative-count change introduces a covariance problem, and two numerical edge cases remain.
1. Invalid verdict — partly fixed.
   statistics.py::design now correctly counts just one informative paper in my original design and withholds inference.
   However, “non-zero contribution” is not an effective-information count. Change the four mean-valued predictors in each alloy from 0.5 to alternating 0.5 ± 0.000001. All 11 papers now count as informative, although almost all slope information still comes from one paper. I reproduced:
   - SE ≈ 0.000292, p ≈ 5.23×10⁻⁵⁸;
   - null rejection 51.15% in 2,000 simulations.
   This is near-degenerate rather than algebraically singular. The definition implements your decision, but does not establish that ten counted papers provide ten meaningful independent contributions. Add a predictor-information concentration diagnostic and an explicit policy for this case; merely increasing the numerical-zero threshold is not a principled solution. This distinction between cluster count and effective information is discussed in MacKinnon, Nielsen and Webb.
2. Informative count in correction and degrees of freedom — partly fixed.
   It is applied consistently in real fits and simulations. If excluded groups have exactly zero scores, using fewer groups increases the correction and, for a positive coefficient, makes the one-sided test more cautious. It remains an approximation, not a guarantee of correct false-positive control.
   But the implementation also drops their scores from the covariance sum. That is not always conservative. A small predictor contrast multiplied by a large residual can matter.
   Concrete counterexample: one alloy, five papers, one record each. Set transformed predictors to:
   x = [1.999, 2.001, 2+1e-10, 2-1e-10, 2]
   y = 300 + 0.01*x + [1e-6, 1e-6, 100, 100, -200-2e-6]
   Grain sizes are x⁻²; outcomes are approximately 100–400 MPa. Under “use available”:
   - current implementation: p = 0.0366;
   - previous all-paper covariance/correction/test: p = 0.1685.
   Fix: retain every group’s score in the sandwich covariance. Apply the informative count separately to the correction and degrees of freedom. Update both implementations and the reference test. The packet’s claim that restoring those scores is an equivalent mutation is false.
3. Display-label database trigger — fixed.
   The incorrect bound is removed, the composition-based analysis remains intact, and the two-compositions/one-label integration test addresses the failure. I found no remaining display-label dependency in the reviewed analysis path. Keeping the historical function for downgrade is appropriate.
4. Numerical rank and unhandled errors — partly fixed.
   The original 9.0/9.000000000000002 case is handled, and exceptions from analyse now become logged refusals.
   New bug: distinct_values counts adjacent gaps. Transformed values [1, 1+1.5e-10] retain the alloy; inserting the intermediate value 1+0.75e-10 makes every adjacent gap fall below tolerance, so the function rejects the entire alloy. Adding an observation should not erase the existing contrast.
   Fix: for the required “at least two” check, compare the full range with the tolerance.
5. Perfect fit/numerical zero — partly fixed.
   The original example is fixed, and the small-real-noise guard passes. The relative threshold is preferable to a fixed MPa cutoff.
   But the threshold uses within-alloy spread, while rounding error also comes from subtracting/fitting the much larger alloy baselines. I reproduced an exact model with baselines between 200–900 MPa and k = 1e-5 that still returns:
   - SE ≈ 7.27×10⁻¹⁴, p ≈ 4.23×10⁻²⁵;
   - estimated scatter ≈ 3.19×10⁻¹³ MPa, marked estimable.
   Fix: account for arithmetic error at the original data scale and conditioning, with stable centering. Add baseline-shift and small-slope perfect-fit tests. This should remain an arithmetic safeguard, not a minimum scientifically meaningful scatter.
6. Smaller points — fixed, with one wording correction.
   Interval limitations, detection rates under both noise assumptions, withholding of estimated-noise results, the zero-coefficient reason, and required evidence level are addressed.
   New minor issue: DETECTION_NOTE hardcodes 5%, although the plan permits another alpha. State the locked threshold dynamically.
7. Tests — partly fixed.
   I found no unjustified removal of earlier protection. Removing the obsolete display-label restriction and updating completion fixtures are appropriate.
   The gaps are in the new tests: they cover exactly-zero contributions, not small contrasts with consequential residuals; they miss the adjacent-gap chain and baseline-sensitive rounding cases. The “independent sandwich” repeats the score-filtering assumption, so agreement does not validate that assumption.
The newly introduced problems are the score omission, adjacent-gap distinctness rule, and hardcoded threshold wording. The remaining numerical-floor problem is an incomplete fix.
I reproduced these cases from the patched packet code; I did not rerun PostgreSQL or the reported 1,138-test suite.
Not safe to merge.
