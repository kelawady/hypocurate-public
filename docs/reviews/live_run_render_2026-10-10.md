# First live runs on Render — record (2026-10-10)

The first runs on the live site, made by the owner from Render's Shell on the worker (`hypocurate-worker`), through the real queue and the step 9b worker. Each run used the claim *"In FCC multi-principal-element alloys, yield strength rises as grain size falls"* and the sources `mpea,tamu_fcc`, with the default sufficiency option (fixed minimum).

**How this record was made:** the owner ran every command. Claude Code has no access to the live database; what is stated here comes from the outputs the owner pasted into the session, or is labelled otherwise.

## Before the runs

- **Sources registered:** `python -m hypocurate.cli sources register mpea tamu_fcc`, run by the owner. This was the first registration on the live database.
  - The registration output was not pasted into the session. The fingerprints were checked from run 3's confirmation text, which names the sealed versions the run used: `mpea version d41959cce6b6; tamu_fcc version 2fad3ccb3dbc`.
  - These match the values computed from the frozen files and sealed in the local development database:

    | Source | Fingerprint |
    |---|---|
    | mpea | `d41959cce6b6e8e319143c8d1dd5473b320b615865358ef9cfce3bc0db848677` |
    | tamu_fcc (with its curation) | `2fad3ccb3dbc32c1ec51e6efcb70a9d17d755bfdfa606cb044f458bd2b37b982` |

  - A fingerprint covers the file bytes and the interpretation settings only, never database ids, so equal fingerprints mean equal sealed versions.
- **The key:** the owner added `ANTHROPIC_API_KEY` to the worker's environment only ("Save and deploy"). The web service makes no model calls and does not have it.

## Run 1 (Q-0001): fixed plan

- **What:** `run … --fixed-plan --ceiling 0.45 --queue`, criterion 14.1a.
- **Result:** reported by the owner as matching the reference numbers exactly: pooled 97 records, 22 alloys, 20 groups, 74 residual degrees of freedom, k = 424.9 ± 64.4, p ≈ 1.3e-6; MPEA alone 424.1 ± 62.2; Texas A&M alone about 1173, coefficient only.
- **Cost:** about $0.04, as reported by the owner. The exact figure was not pasted.
- **The Analyst's wording,** which led to the fix below:
  - a garbled sentence, "Because of the the estimate is positive, the direction the claim describes, the result points the way the claim describes";
  - "at least 10 groups" without its "(met)" status.

## Run 2 (Q-0002): Planner, failed

- **What:** `run … --ceiling 0.50 --queue`.
- **Result:** `planner_failed: the Planner gave no usable plan (invalid_plan)`.
- **Stored stage** (stage 8, settings version 1): `attempts: ["invalid_plan", "invalid_plan"]`, with no reason stored, because the code at the time stored none.
- **Calls:** two Planner requests, both recorded as succeeded:
  - 3,357 input and 379 output tokens, $0.021008;
  - 3,416 input and 395 output tokens, $0.021564 (the extra 59 input tokens are the corrective note).
- **Cost:** $0.042572.
- **Cause:** the Planner's output description told the model "exactly the keys domain_matches, claim_scope, outcome, exclusion_rules and narrower … Nothing else", five keys. The check required six, including `stated`.
  - **How it arose:** `stated` was made required in e123f11 (2026-10-07 16:16 UTC), and the description was not updated.
  - **Why it went unseen:** every earlier Planner success, all local, ran before that change.
  - **Why the tests missed it:** they use ready-made answers that include `stated`.
  - **Why the retry failed too:** the corrective note named only the code, so it did not help the model.
- **The fix:** branch `fix-agent-contracts`, merge `51257cb`, live 2026-10-10 23:43 UTC; `docs/reviews/fix_agent_contracts_summary.md`.
  - The description is generated from the check's own key list.
  - Every refused attempt stores a specific reason in code's words, and the retry's note names it.
  - The Analyst gets the direction as a whole sentence and the minimums in one sentence with every status.
  - Contract tests compare each agent's request with its check.
  - **Before the merge, a local live check ($0.058):** the Planner, accepted on its first attempt, gave the reference plan in every field; a fixed-plan run reproduced the reference numbers.

## Run 3 (Q-0003): Planner, confirmed, completed

- **Dispatched with the Planner after the fix was live.** The Planner's answer was accepted. The run waited at the rules lock: 1 model call, $0.017640.
- **Confirmed by the owner:** `confirm 3 --by "Khalid El-Awady" --queue`, recorded 2026-10-10 23:53:27 UTC.
  - **The question as tested, as confirmed:** yield strength against grain size, in multi-principal-element (high-entropy) alloys (as the claim states); phase class FCC (as the claim states); test type tension (assumed); room temperature, 20 to 25 °C (assumed); excluding records with a grain size below 0.1 µm.
  - **Narrowing:** none ("proceed; no part without records"). Candidate records per part: 182 each.
  - **Plan fingerprint:** `e5d96077b6fba400236ddee4a30731acfd62169866c3afde5696b8e55ef96a5d`.
- **The worker:**
  - It took the run up within about a minute of the confirmation: `queue` showed `waiting` ("a worker (confirmed)") at 16 s and 34.5 s, then `running` at the curation and analysis stages, with a heartbeat 2.5–3.5 s old.
  - It then completed the run, and the queue was empty.
  - No recoveries.
- **Results:** completed; sufficient in the sources searched; verdict supported under the stated model, in the sources searched; evidence level 6.

  | Set | Records | Alloys | Groups | Residual df | Estimate (MPa·µm^0.5) | Standard error | p (one-sided) |
  |---|---|---|---|---|---|---|---|
  | Pooled | 97 | 22 | 20 | 74 | 424.9 | 64.4 | 1.3e-6 |
  | MPEA alone | 76 | 13 | 19 | 62 | 424.1 | 62.2 | 1.1e-6 |
  | Texas A&M alone | 21 | 9 | 1 | 11 | 1173.3 | — | — (coefficient only, too few groups) |

  - **Sensitivity:** all 9 sets agree with the pooled result. Estimates run from 393.5 (without the group with the largest share of slope information: p ≈ 1.9e-4, 89 records, 19 groups) to 432.4 (scope not confirmed included).
  - **Spread of the slope information:** effective number of groups 3.94 of 20 informative; largest share 38.7%.
  - **Calibration:** significant in 8.6% (estimated noise) and 8.3% (fixed noise) of simulations with no effect, against a nominal 5.0%. Flagged as over-confident; a flag, not a gate.
- **Equal to run 1,** as the owner reports, apart from the calibration shares (see open items), and equal to the approved reference numbers (CLAUDE.md, "Reference numbers").
- **The Analyst's text** (labelled "narrative not verified"):
  - it uses the direction as a whole sentence and the minimums with every status, "at least 10 informative groups (met)" included;
  - its closing sentence ("A cleaner test would need more groups that each report grain size alongside yield strength") is the model's own suggestion, beyond the facts it was given.
- **Calls:** 3 model calls; 10,447 input and 2,608 output tokens; **$0.093948**.
  - Before the confirmation, 1 call: the Planner, $0.017640.
  - After it, 2 calls, $0.076308. The run raised no flag for the Critic, so both were Analyst requests (settings version 4, the post-fix instruction). The stored Analyst stage, read by the owner:
    - `attempts: ["malformed", "ok"]`;
    - `attempt_reasons: ["missing output field: report", null]`;
    - failure details for attempt 1: no field header at all (`header_count` 0), no completed marker, the answer not empty.
  - **So the first Analyst answer was refused for its form, not its content.** The model wrote its explanation as plain text, without the `[[ ## report ## ]]` … `[[ ## completed ## ]]` form it is asked for, so DSPy could not read it.
  - **What did not happen:** no wording, placement or number rule was applied, because the text was never read that far.
  - **The correction worked:** the retry's note named the reason (the fix's new behaviour), and the second answer was accepted.
  - **The cost of the slip:** about $0.038.
  - **It has happened before:** the same form slip occurred once in step 8b (local run 1's first Analyst answer).

## Costs

| Run | What | Calls | Cost |
|---|---|---|---|
| 1 | Fixed plan | not pasted | about $0.04 (owner) |
| 2 | Planner, failed `invalid_plan` | 2 | $0.042572 |
| 3 | Planner, confirmed, completed | 3 | $0.093948 |
| | **Total on Render** | | **about $0.18** |

In addition, the local live check of the fix cost $0.058, on the development database. Every run stayed within its ceiling, and the month is far below the $50 cap.

## Open items

For steps 10 and 11 (not built here):

1. **The simulation seed is not tied to the analysis.** On identical data, the calibration's share of significant tests with no effect was 7.8% in one run and 8.6% in another (owner's comparison of runs 1 and 3). The seed comes from the whole-run fingerprint, which differs between runs with the same data and plan. Already in the backlog: an analysis-specific seed and about 10,000 simulations before the final evaluation.
2. **"10 independent groups" in the confirmation text** should be "10 informative groups". The paper minimum counts informative groups (register, `fixed_minimums`), as the statement and the Analyst's minimums sentence say (`pipeline/confirmation.py`).
3. **`queue` shows the stage as "none" while a run waits.** It should say what the run waits at, for example the rules lock.
4. **The label printed during `confirm` is the pre-confirmation label.** The text the person confirms is labelled "not verified by code and, in this version, not confirmed by a person", the label of the state being confirmed. The wording shown at the moment of confirmation should be reconsidered.

Also open:

5. **The Analyst sometimes answers without its output form.** Run 3's first attempt was refused as malformed, reason "missing output field: report"; one such slip also happened in step 8b. The correction handles it, at the cost of a second call. If it recurs, consider whether the request's form instructions can be made clearer. Not a correctness issue.
6. **`ANTHROPIC_API_KEY` is not declared in `render.yaml`.** It is unconfirmed whether a Blueprint sync keeps a key added only in the dashboard; check it after the next `render.yaml` change.
7. **The GitHub suite times of the fix** (branch 21 min 45 s, main 32 min 16 s) are not yet in `fix_agent_contracts_summary.md`.
