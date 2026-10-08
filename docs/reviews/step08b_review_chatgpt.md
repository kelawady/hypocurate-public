# Step 8b — second-model review (ChatGPT), 2026-10-07

Verdict: **not safe to merge.** Text as received by the owner and passed to Claude Code (the packet link in the
original pointed to the owner's local copy of `docs/reviews/step08b_review_packet.md`).

---

I found five issues to fix before merging. These are ordinary implementation mistakes within your stated threat model.
References below are to files quoted in the review packet (`step08b_review_packet.md`).

1. High — A narrower question can bypass its stored plan and source-version check.
   Files: pipeline/queries.py, pipeline/orchestrator.py.
   queries.dispatch() defaults to fixed_plan=False. The orchestrator checks the original’s narrower plan and source fingerprints only inside the fixed_plan branch. The CLI supplies the right flag, but the shared dispatch function does not enforce it.
   Failing sequence: create a narrower question, register a newer source version, then call queries.dispatch(engine, vid) normally. The orchestrator follows the Planner path, bypassing narrowing_sources_changed and the requirement to use the stored narrower plan.
   Fix: derive this behavior from narrower_of_run_id in dispatch and the orchestrator; do not depend on a caller remembering a flag. Add a database backstop and a regression using the default dispatch arguments.
2. High — Recorded settings need not be the settings actually used.
   Files: pipeline/agents/runstage.py, planner.py, critic.py, analyst.py.
   open_stage() records the settings version bound at dispatch. Each role then builds its request from the current global SETTINGS, rather than that recorded version.
   Failing case: dispatch a run, change an instruction or reasoning setting in a deployment, then execute the queued run. The request uses the new settings while the audit record names the old version. Keeping the model name unchanged is enough to expose this discrepancy.
   Fix: load instruction, model, limits and options from the invocation’s recorded settings. Test dispatch under version A and execution after current settings become B.
3. High — A recording or reservation failure does not stop further paid requests.
   Files: pipeline/agents/critic.py, pipeline/orchestrator.py.
   The Critic stops batching only for spending caps and ceiling_reached. It continues after recording_failed and reservation_failed. The orchestrator also treats only spending failures as terminal, so it can subsequently call the Analyst.
   Reproduced: running the actual Critic loop with two batches and mocked boundaries, either failure on the first batch caused a second call attempt.
   Keeping an unresolved reservation counted, and eventually refusing completion, does not prevent those subsequent requests.
   Fix: propagate accounting failures as run-level stops. Leave unresolved calls/runs open for recovery, with no later agent request. Test both another Critic batch and the subsequent Analyst.
4. Medium — The Analyst’s numerical guarantees are stronger than its checks.
   Files: pipeline/agents/text_checks.py, analyst.py, pipeline/analyst_names.py.
   Reproduced with the actual checker: all these pass on an insufficient run:
   - “The outcome is {outcome_wording}. The p-value is zero.”
   - “… The estimate is forty MPa.”
   - “… The estimated effect is ½ MPa.”
   These contain no decimal digits, but they plainly introduce numerical claims.
   There is also a separate phrase-only loophole: count_groups exposes the informative-group count individually. I reproduced an accepted explanation using it separately. The test claiming no individual paper figure escapes misses this name.
   Fix: put numerical assertions in code-rendered sentences and explicitly distinguish unverified model commentary. Do not try to solve this with an expanding list of number-word regexes. Either remove the separate informative-count fact or explicitly revise the phrase-only requirement. The current blanket label is not justified; “placeholder values copied from the run record; narrative not verified” is more accurate.
5. Medium — Ordinary malformed Critic JSON crashes instead of leaving an entry unclassified.
   File: pipeline/agents/critic.py.
   Reproduced: {"7": {"class": []}} and the equivalent object-valued class raise TypeError at membership testing against CRITIC_CLASSES.
   This escapes the documented per-entry failure handling and leaves the stage unfinished.
   Fix: check that the class is a string before membership testing. Add nested wrong-type cases to the role validators; the existing Critic tests cover invalid strings, but not these valid-JSON shapes.

On the remaining questions:
- Code decides: I found no decision path reading the Critic’s class or reason, or taking a verdict/evidence level from Analyst prose. The Planner legitimately affects inclusion through scope and exclusions. Its temperature bounds also populate rules[RANGE_RULE], so “no rules come from the model” needs that qualification. The fixed eligibility policy, statistical model, calibration and query sufficiency option otherwise remain outside its answer form.
- Claim interpretation remains unchecked. make_check() does not receive the claim text. A valid FCC answer to a BCC claim can pass, as can an incorrect stated/defaulted mark. Worst case: a valid computation and “supported” verdict attached to the wrong scientific question. At minimum, enforce that values marked defaulted actually equal the defaults, show the interpreted scope and exclusions prominently, and describe stated/defaulted marks as the Planner’s reading. Domain confirmation alone does not verify scope.
- Narrowing itself: the decision receives structural counts, not outcome values, and removes exactly the zero-count parts of the parsed scope. Those counts are candidate availability, not proof that records survive eligibility or meet minimums. The original’s no-plan/no-record/no-verdict path is guarded; the narrower child has finding 1.
- Facts and summaries: the normal withheld path appears to exclude outcome-derived estimates and calibration, retaining fixed-noise simulations. The sensitivity labels and calibration summary follow stored results. The direction note follows the locked alternative, which is only as faithful to the claim as the Planner’s interpretation. The live prose about a p-value being “more favourable than it really is” overstates what calibration establishes; it does not estimate this particular p-value’s error.
- Access and safeguards: I found no additional source-data disclosure in the reviewed request builders. Retries use fixed failure notes, and tools are absent in the supplied request tests. Emptying the Commentator’s lists and removing its gap-report handoff are consistent. Preloading scipy is acceptable for the explicitly limited file-guard tripwire.
- Migration and spending: 0006 is additive, with sensible rollback tests and no earlier function replacement. Its guards do not close finding 1. The existing run/month reservation lock order appears preserved. The live-set ceiling works for the supplied sequential harness; it is not an independently enforced concurrent experiment-wide cap.
- Tests: the fixture/access-test replacements generally preserve the relevant protections. But the supposed orchestrator Critic-failure test uses reference data with no flags, so it can pass without exercising a Critic failure at all. The supplied suite also misses the five cases above. Mutation-test success does not cover those omissions.

Smallest live Critic test: one capped call on a marked constructed-data run with a small flagged batch. Inspect the actual request, accepted/refused classifications and recorded cost; confirm the resulting decisions remain unchanged. No large live evaluation is needed before this limited, advisory role is used.

I reproduced the pure-checker failures and the Critic batching behavior with mocked database/provider boundaries. I did not rerun PostgreSQL, migrations, Docker, the full suite or live provider calls.

Not safe to merge.
