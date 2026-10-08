# Step 8b — second-model confirmation round (ChatGPT), 2026-10-08

Verdict: **not safe to merge** (the four presentation fixes closed; one remaining issue: the Critic's displayed
advice lacks an explicit unverified-advice label). Text as received by the owner and passed to Claude Code. The owner
decided to merge once that label is in with its test and the GitHub run on the new head is green, without another
review round (recorded in `docs/reviews/step08b_summary.md`).

---

The four presentation fixes are closed. One small but material issue remains: the Critic’s displayed advice lacks an explicit warning that its classification and reason are unverified.

1. Results statement — fixed.
   statement.py now handles “coefficient cannot be fitted” before attempting numeric formatting. The other branches distinguish withheld results, coefficient-only results and valid inference. I reproduced the previously failing not-fitted case successfully.
2. Concentration line — fixed.
   _spread_line() is now independent of whether a p-value exists. A coefficient-only result rejected for concentrated evidence shows the effective paper count, informative count and largest share. I reproduced this case.
3. Format version — fixed.
   Rendering consistently uses the current format and explicitly identifies a different completion-time version—or an unrecorded version. The register and summary now describe this accurately: the recorded version documents completion history; it does not reproduce historical wording.
4. Statement before labelled Analyst text — fixed.
   run and dispatch now reuse show, rather than printing the orchestration report’s raw explanation. show puts the statement first and supplies Analyst text through the labelled wrapper, only when the statement exists. I found no remaining bypass in these three command paths.
5. Critic scope and presentation — partly fixed.
   Restricting it to flags naming at least two records is sound for its comparison role. Single-record flags remain visible and retain code’s checks; what disappears is optional model commentary, not a safeguard. Separate flag blocks and the instruction to judge each independently are appropriate.
   The displayed label is insufficient. In agents/critic.py, flag_display() emits the classification and reason under the key critic; cli_runs.show() passes that through without an unverified-advice warning. “Same measurement reported twice” can therefore look like an established finding.
   The second live call supports shipping only as explicitly unverified advice. “Zero wrong classes” under the grading scheme does not establish reliability: four unsupported “same measurement” answers among six judgement cases remain substantive errors for a reader.
   Add a visible label beside this output: “Language-model advice; classification and reason not verified; not used in decisions.” Add a display test requiring it. I would not require another tuning round or live call before merging once that is done.
6. Tests — fixed; no protection loss found.
   The updated multi-record fixtures keep request, failure and disclosure tests meaningful after the scope change. Single-record exclusion is tested explicitly. The renderer changes strengthen coverage; replacing the historical-format expectation follows the new owner decision.

No other new material issue found within this review’s scope. I reproduced the targeted renderer cases, but did not rerun PostgreSQL integration tests or live calls. The packet omits the full statement fixture and answer-key contents, limiting independent reproduction of those checks.

Not safe to merge.
