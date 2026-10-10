# Fix: agent contracts — summary for review

Date: 2026-10-10. Branch: `fix-agent-contracts` (from `main` at `4b780c4`). **The owner's decision:** fix, then merge without a ChatGPT round once the local live check passes and the GitHub run is green ("the live call is the real test here").

## Why

On 2026-10-10 the owner ran the first two live runs on Render, through the real queue and worker.
- **Run A (fixed plan)** reproduced the reference numbers exactly ($0.04). Its Analyst text had two wording faults:
  - a garbled sentence, "Because of the the estimate is positive, the direction the claim describes, …";
  - "at least 10 groups" without its "(met)" status.
- **Run B (Planner)** failed `planner_failed: invalid_plan` twice ($0.0426).
  - **The cause:** the Planner's output description told the model "exactly the keys domain_matches, claim_scope, outcome, exclusion_rules and narrower … Nothing else", five keys. The check (`read_answer`) required six, including `stated`.
  - **When it began:** `stated` became required in e123f11 (2026-10-07 16:16 UTC), and the description (82aab3c) was never updated.
  - **Why it went unseen:** every local Planner success ran before that, from 12:32 to 12:50 UTC on 2026-10-07, so no live Planner answer had been checked under the current rules.
  - **Why the tests missed it:** they use ready-made stub answers that already contain `stated`.
  - **What the records could not say:** the stored records could not prove the cause, because answer text and the specific reason were not stored. The live check below confirms it: with the corrected description, the model gave `stated` on its first attempt.

## What was built

1. **The Planner's output description comes from the check's own key list.**
   - `planner.ANSWER_KEYS` (ordered) is the one definition. `KEYS = frozenset(ANSWER_KEYS)`.
   - `OUTPUT_DESCRIPTION` is generated from it, so the two cannot drift apart again.
2. **A specific reason for each refused attempt, for every agent.**
   - **The common interface** (`call_agent`) keeps one reason per attempt in `AgentResult.reasons`.
   - **Every role stores them** as `attempt_reasons`, beside `attempts`: the Planner's, Critic's and Analyst's stage output, and the curation summary.
   - **The retry's corrective note** names the reason: "(code: fixed text; specifically: reason)".
   - **Reasons are code's own wording:** counts, and the role's own keys, scope parts, names and rules. They never contain the answer's text, a key or value the model wrote, a provider's text or an error's text.
   - **The Planner's reasons:**
     - "missing key: stated";
     - "test_type is marked as not stated by the claim but differs from the default";
     - "a key that is not allowed" (never naming the key);
     - "alloy_class: a non-empty list of distinct allowed values", and so on;
     - one fixed reason for a plan the template refuses (`PLAN_INVALID_REASON`), because the validator's own message can quote what it was given.
   - **The Analyst's reasons:** "the text does not use {outcome_wording}", "digits outside placeholders: 2", "wording rule: forbidden: proves", and the placement rule below.
   - **The Critic and the Curator:** their checks only refuse unreadable JSON, with a fixed reason.
   - **An answer DSPy cannot parse:** gets a reason from its form facts only, such as "missing output field: plan".
3. **The Analyst's direction sentence.**
   - `{direction_sentence}` replaces the clause `{direction_note}`. Its value is the whole sentence code's statement already prints ("The estimate is positive, the direction the claim describes.").
   - The statement is unchanged.
4. **Whole sentences stand alone.**
   - **The rule:** `text_checks.SENTENCE_NAMES` lists model, scope source, direction, minimums, calibration summary and group definition. Each must stand as a sentence of its own.
   - **Where it may stand:** after the start of the text, a sentence's end, a line start or a list marker. It must be followed by the end, a line break or a capital letter.
   - **What happens otherwise:** the text is refused as `wording_refused`, with the reason "{name} is a whole sentence: place it as a sentence of its own".
   - **The instruction** names exactly these, generated from the same tuple. Run A's frame "Because of the {direction_sentence}, …" is refused.
5. **The minimums with their status.**
   - **One sentence:** `{minimums_sentence}` gives every minimum with its status: met; not met; "not met; waived: use what is available"; or "not assessed: no dataset was frozen".
   - **No bare minimums:** the `{minimum_records}`, … names are removed, so a minimum can no longer be shown without its status.
   - **The groups:** their status is shown, never their count. The informative-group count stays a paper figure, as in step 8b fix round 1, finding 4.
6. **The register:** four entries are reworded, each with its earlier wording in its history, decided by the owner on 2026-10-10. They are `planner_answer`, `request_failure_policy`, `analyst_facts_only` and `analyst_text_checks`. New settings are named: `ANSWER_KEYS`, `OUTPUT_DESCRIPTION`, `PLAN_INVALID_REASON`, `correction_note`, `parse_reason`, `SENTENCE_NAMES`, `placement_problems`, `minimums_sentence`, `direction_sentence`.

**Not changed:** the statistics, the decisions, code's statement, the access layer's allow-lists, the migrations, `render.yaml`, the workflows, the Dockerfile and the dependency locks.

## Tests

- **Failing tests first** (commit `fa1820f`): 47 new tests failed on `main` (`~/hc-work/fix-agent-contracts/before.log`).
- **Contract tests** (`tests/test_agent_contracts.py`, new), one or more per agent:
  - **The Planner:** the keys named in the output description equal the check's keys; an answer with exactly the keys the model is told passes. Both failed on `main` for run B's reason: `stated` was missing.
  - **The answer form:** the form's keys and scope parts are those the check requires.
  - **The Critic:** the entry keys named are those `classify` accepts, and the reason limit and classes are the check's.
  - **The Curator:** the entry keys and targets are those its check reads.
  - **The Analyst:** every required name is named in its instruction, and the whole sentences it is told to place alone are exactly those the check enforces.
  - The Critic's and the Curator's contracts already held; their tests pass on `main` and guard against drift.
- **Reasons:** each Planner reason is stored and named in the retry. A planted-value test, with four planted keys and values, shows a reason never carries the model's text. Each Analyst refusal has its reason, and the parse reason is checked case by case.
- **The Analyst's wording:**
  - the direction sentence over every value it can take (positive, negative, zero), and none without an estimate or the claim's direction;
  - run A's frame refused;
  - six accepted placements and six refused ones;
  - the minimums sentence in all four states, every minimum with a status, no group count;
  - every value of a whole-sentence name is a complete sentence;
  - the facts hold no bare minimum;
  - every placeholder the instruction names is a fact the Analyst is given.
- **Earlier tests changed with the owner's decision (assertions kept):**
  - `test_analyst.BELOW`: the template uses `{minimums_sentence}` instead of `{minimum_records}`.
  - `test_a_run_below_the_minimums_offers_no_estimate_names`: checks `minimums_sentence` instead of `minimum_records`.
  - `test_the_facts_carry_the_code_built_sentences_units_and_the_nominal_level`: checks `direction_sentence` instead of `direction_note`.
  - `SENTENCES`: the direction is placed as its own sentence.
  - `test_agent_core::test_an_unusable_answer_is_corrected_once_with_a_fixed_note_and_never_the_answer`: the note now includes the reason, and the literal reason is checked.
- **The whole suite:** 2,215 tests, all passing locally (36 min 37 s) on `436b518`. The final local run before the push and the GitHub suite step are given below.

## Mutation checks

17 faults (m01–m17) were applied to a scratch copy one at a time, and **all 17 were caught**. The control is clean.
- **The first run was discarded:** the scratch copy lacked `data/`, so the control failed 30 tests. It is kept as `mutations_run1_no_data_discarded.log`.
- **m17 at first survived:** it makes the parse reason always empty. The new test computed its expectation with the same function, so it agreed with the fault. That test now checks the literal reason, and a direct test of `parse_reason` was added (`2035bbc`). m17 is now caught.
- The specifications and outputs are in `~/hc-work/fix-agent-contracts/`.

## Reference runs against `main`

- **The statistics reference dump:** 0 differing leaves.
- **The five orchestrator dumps** (fixed plan; Planner FCC; Planner BCC; partly sufficient; narrower question), every call to the stub. Only these differ:
  - the new `attempt_reasons` lists (`[null]`);
  - the Analyst's facts: `direction_note` and `minimum_*` removed, and `direction_sentence` and `minimums_sentence` added; no other fact changed;
  - the reserved maximum cost (`max_cost`) of the Planner and Analyst calls, up to $0.0014, because the requests are slightly longer.
- **Unchanged:** code's statement, the decisions, the results and the `show` output.

## The live check (local development database; the owner's go, at most $0.50)

| Run | What | Result | Cost |
|---|---|---|---|
| 13 (Q-0013) | Planner, the FCC claim, ceiling $0.25. It ran in-process through `orchestrator.work_guarded` under a real claim, so DSPy's parser could copy the raw answer to `~/hc-work/fix-agent-contracts/live/planner_raw.txt`, outside the repository (as in 8b's diagnostic). | Accepted on the first attempt; the raw answer includes `stated`. **The plan equals the reference plan in every field.** Question as tested: tension and room temperature assumed (the claim does not state them). Left `waiting`, not confirmed. | $0.0200 |
| 14 (Q-0014) | Fixed plan, the same claim, ceiling $0.25, through the real command line and guarded worker child. | Completed, sufficient, supported, level 6. Pooled 97 / 22 / 20 / 74, k = 424.9 ± 64.4, p ≈ 1.3e-6; MPEA 424.1 ± 62.2; Texas A&M 1173.3, coefficient only. **The Analyst passed on the first attempt.** `{direction_sentence}` stands as its own sentence; `{minimums_sentence}` gives all four minimums "(met)", groups included. | $0.0380 |

**Total: $0.0580.**

**Points in the Analyst's narrative for the owner** (labelled "narrative not verified"; not in this fix's scope):
- It wrote "Borg et al. two thousand twenty": a year in words, to avoid writing digits.
- It says the over-confident method means "the nominal p-value overstates the strength of the evidence", an interpretation beyond the facts given.

## Open

- **Run 13** on the local database is waiting for a person's confirmation (owner: confirm or cancel).
- **Run B on Render** is to be re-run by the owner after the deploy.
- **The scope notes** (`{scope_test_type}` …) are still clauses the Analyst sets in its own sentences. They were not part of run A's fault and are unchanged.
- **The register entry `agent_models`** is unchanged. The Analyst's instruction changed, so the next run records a new settings version (append-only, automatic).
