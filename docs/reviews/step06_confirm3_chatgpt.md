# Step 6 — second-model confirmation, round 3 (ChatGPT, 2026-10-06)

Confirmation review of `docs/reviews/step06_fix4_packet.md` (branch `step-06-eligibility`). Saved verbatim as the owner gave it. The owner's rule: no record connected to a definite conflict enters the primary set under any plan; a survivor is allowed only in the sensitivity set `conflicts_survivor_value` (see `docs/reviews/step06_summary.md`).

---

1. A, B, C order dependence — fixed. I tested all six ID assignments × all 24 input orders: 144 combinations, with identical decisions and memberships across every set, counts and freeze fingerprints. Resolving whole connected components removes the previous pair-order dependency.
2. Survivor choice — fixed. Selection uses DOI presence, the locked source priority, row number and stable source/origin/item identity. Database IDs affect internal component representation, but no longer determine the survivor. The outcome is deterministic for the same evidence and locked plan.
3. Conflict exclusion — not fixed to your stated requirement. A plan can still map values_disagree to duplicate_counted_once. For an exact chain A–B touching conflict B–C, I reproduced:
   - A admitted to primary;
   - B and C excluded as counted-once copies;
   - no objection from either the rule guard or freeze checker.
   Required correction: primary must always exclude the entire conflict-connected component. Permit a survivor only in conflicts_survivor_value. Enforce that at validation, application and freeze. The freeze currently rejects more than one member of a conflict component; your rule requires rejecting any member.
4. Freeze verification of exact chains — fixed. It reconstructs chains from Checks’ flags rather than trusting Inclusion’s survivor decisions. It retains the middle record when establishing connectivity even if that record is outside primary. Selecting A and C from A–B–C correctly fails. It shares the component-building helper with Inclusion, but independently checks membership. The separate conflict-policy defect is item 3.
5. Shared-function rather than full-pipeline chain test — fixed adequately for this scope. Exercising the actual matching, selection and fingerprint functions covers this algorithmic defect. The pipeline permutation tests separately cover storage and integration. Given the current adapters’ limitations, another end-to-end chain fixture is not a merge blocker.
New issues: none beyond the conflict-policy mismatch above.
I ran targeted reconstructed-code tests, not the reported 901-test database suite.
Not safe to merge.
