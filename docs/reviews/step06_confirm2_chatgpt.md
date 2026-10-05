# Step 6 — second-model confirmation, round 2 (ChatGPT, 2026-10-06)

Confirmation review of `docs/reviews/step06_fix3_packet.md` (branch `step-06-eligibility`). Saved verbatim as the owner gave it. The owner asked for the new problem to be fixed, with tests that fail on the code before it (see `docs/reviews/step06_summary.md`).

---

1. Mixed groups — fixed for the A, B, C case. The exact A–B relationship survives as its own flag. Pipeline tests check counted-once handling, and the freeze test bypasses eligibility to demonstrate that the retained pair independently causes refusal. The freeze checker no longer relies solely on the group label.
2. Paper identity — fixed. Unequal reference text now means unknown. Unequal normalized DOIs still establish different papers. Matching uses the shared function, including sensitivity sets.
3. Non-unique exact matches — fixed for primary. Those records remain in an unresolved-identity group, which primary excludes regardless of the possible-duplicate choice. Counting possible duplicates separately cannot override that exclusion. They may enter the explicitly named sensitivity set, as intended.
4. “Definite first” mutation — the equivalence claim is correct for that specific change. With one survivor ordering, resolving a subgroup before its enclosing counted-once group cannot remove the enclosing group’s highest-priority survivor. If possible duplicates are counted separately, their group rule removes nothing anyway.
   That does not establish that ordering among definite pairs is harmless. The new issue below demonstrates otherwise.
5. The two additional label-over-pair fixes — fixed. Retaining the exact pair inside a conflict-labelled group gives the freeze checker that relationship. Keeping a conflict confined to its definite pair correctly avoids excluding a third record whose links are only possible.
New issue: overlapping retained exact pairs make primary depend on database IDs.
I reproduced this with identical conditions and values:
- A: MPEA, DOI D, reference text X.
- B: Texas A&M, DOI D, reference text Y.
- C: extract, no DOI, reference text Y.
Checks finds A–B exact through DOI, B–C exact through reference text, and A–C possible. Choose the permitted “possible duplicates counted separately” plan and supply another grain size.
The result changes with pair-processing order:
- A–B first: B is excluded; processing B–C then leaves C. A and C survive.
- B–C first: C is excluded; A–B then excludes B. Only A survives.
Swapping record IDs produced these two results. Both passed the freeze invariant checker. This can change counts and statistical results without changing the plan or source evidence.
Resolve overlapping definite pairs using a stable, explicitly defined procedure based on the survivor priority—not generated flag or record IDs. Add a regression that permutes IDs and insertion order and compares the frozen memberships.
These conclusions use the packet and targeted reconstructed-code probes; I did not rerun the reported 896-test database suite.
Not safe to merge.
