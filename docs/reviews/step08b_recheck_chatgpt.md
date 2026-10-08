# Step 8b — second-model re-check (ChatGPT), 2026-10-07

Verdict: **not safe to merge** (the five original findings closed; four new issues in the results statement and its
presentation). Text as received by the owner and passed to Claude Code.

---

The original control-flow findings are closed. The new results statement and its presentation still need fixes.

1. Narrower question — fixed.
   Dispatch and both orchestrator phases now derive the path from the question’s link. The database independently checks the stored narrower-plan content and source fingerprints. The default-argument bypass is closed. I found no legitimate path broken by these guards.
2. Settings — fixed.
   All four roles now obtain instruction, model, limits and options from the invocation’s recorded settings. The tests exercise dispatch under version A followed by current settings changing to B, including Critic batching.
3. Accounting failures — fixed for the reviewed execution paths.
   Both failures stop Critic batching and propagate through the Planner, Critic and both Analyst paths. No subsequent agent call or completion follows. The replacement tests actually raise flags and exercise these failures.
4. Answer shapes — fixed for the identified defects.
   Type checks precede vocabulary membership. The expanded tests cover nested wrong-type values across the roles. They provide substantially better coverage, though not proof against every possible malformed response.
5. Results statement — partly fixed.
   Rendering from stored results is reasonable, but pipeline/statement.py has three gaps:
   - A completed “coefficient cannot be fitted” run crashes the renderer. With withheld=False and estimate=None, _analysis_lines() calls display.coefficient(None). I reproduced the resulting TypeError. Add an explicit not-fitted branch; the fixture claiming to cover every outcome omits this one.
   - Concentration is not always shown. Its line requires a non-null p-value. Consequently, a coefficient-only result with inference_reason="evidence_concentrated" hides precisely the concentration figures explaining its failed validity check. Show them whenever available. Comparing effective groups with that run’s informative-group count, without another threshold, is the right descriptive presentation.
   - The recorded format version does not select the renderer. build() always uses current code. After version 2 arrives, a version-1 run gets version-2 wording; retaining the old expected hash does not preserve the old renderer. Either dispatch rendering by recorded version or explicitly define this as rendering historical results with current wording. The present claim that wording follows the recorded version is unsupported.
   Otherwise, the caution rules follow the stored flags and labels. The revised calibration caution appropriately distinguishes method calibration from the error of this particular p-value.
6. Analyst label and separation — partly fixed.
   The approved label honestly describes the narrative’s status, and show separates it from the statement.
   But immediate run/dispatch output still prints RunReport.explanation without the label or fixed statement. cli_runs._run() prints the orchestration report directly. Users can therefore encounter unlabelled model prose first. Use the same labelled presentation for every completed-run output.
7. Planner’s reading — fixed within decision B.
   Defaulted parts are checked against the same defaults supplied to the Planner, ignoring list order. The remaining-risk label is fair: code checks consistency, not whether the claim actually states those values. Human confirmation remains explicitly deferred.
8. Live Critic — fixed as a transport/integration check; reasoning remains unverified.
   The supplied request inputs contain metadata and flag categories, not compared measurements. This is stored request-input evidence, not a complete captured wire request.
   Comparing two separate single-record flags is incorrect reasoning, although it cannot change decisions. Yes: instruct it to assess each flag independently using only that flag’s records, and permit cannot_tell. This needs no architectural change.
9. Changed tests — fixed; no lost protection identified.
   The race test still checks the waiting-reader/checkpoint interaction and now covers ordinary and narrower runs. Replacing the vacuous Critic-failure test improves coverage. Missing tests are the not-fitted statement, concentration without inference, historical format rendering, and labelled immediate CLI output.

New issues introduced: the statement’s missing not-fitted branch, incomplete concentration display, ineffective historical-format selection, and inconsistent CLI presentation described above.

I reproduced the renderer failure locally. Database guards and integration results were reviewed from the packet; I did not rerun PostgreSQL, the full suite or live calls.

Not safe to merge.
